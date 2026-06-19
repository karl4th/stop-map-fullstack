import asyncio
import logging
from collections import defaultdict

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.core import api
from app.core.menu import role_menu
from app.core.photos import send_card_photos
from app.keyboards.inline import engineer_decision_keyboard, manager_review_keyboard, user_approval_keyboard, violator_accept_keyboard
from app.keyboards.reply import cancel_keyboard, fix_done_keyboard, skip_keyboard
from app.states.manager_fix import ManagerFix, ManagerReview

logger = logging.getLogger(__name__)
router = Router()

_photo_locks: dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)


# ── Нарушитель нажал "Принять" ────────────────────────────────────────────────

@router.callback_query(F.data.startswith("ack:"))
async def cb_acknowledge(callback: CallbackQuery):
    card_id = int(callback.data.split(":")[1])
    try:
        await api.bot_acknowledge(card_id, callback.from_user.id)
        await callback.message.edit_reply_markup(reply_markup=violator_accept_keyboard(card_id))
        await callback.answer("✅ Принято. Отправьте исправление после устранения.")
    except Exception as e:
        err = str(e)
        if "уже" in err or "обработана" in err or "нельзя" in err.lower():
            await callback.answer("ℹ️ Карта уже обработана", show_alert=True)
            await callback.message.edit_reply_markup(reply_markup=None)
        else:
            await callback.answer(f"❌ {err}", show_alert=True)


# ── Нарушитель нажал "Отправить исправление" ─────────────────────────────────

@router.callback_query(F.data.startswith("fix:"))
async def cb_fix_start(callback: CallbackQuery, state: FSMContext):
    card_id = int(callback.data.split(":")[1])
    await state.set_state(ManagerFix.waiting_description)
    await state.update_data(card_id=card_id, photo_ids=[])
    await callback.message.answer(
        "📝 Опишите что именно было сделано для устранения нарушения:",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


# ── Нарушитель вводит описание устранения ────────────────────────────────────

@router.message(ManagerFix.waiting_description)
async def fix_got_description(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=await role_menu(message.from_user.id))
        return

    await state.update_data(fix_description=message.text.strip(), photo_ids=[])
    await state.set_state(ManagerFix.waiting_photos)
    await message.answer(
        "📸 Отправьте фото после устранения (можно несколько).\n"
        "Когда закончите — нажмите кнопку ниже.",
        reply_markup=fix_done_keyboard(),
    )


# ── Нарушитель отправляет фото ────────────────────────────────────────────────

@router.message(ManagerFix.waiting_photos, F.photo)
async def fix_got_photo(message: Message, state: FSMContext):
    async with _photo_locks[message.from_user.id]:
        data = await state.get_data()
        photo_ids = data.get("photo_ids", [])
        photo_ids.append(message.photo[-1].file_id)
        await state.update_data(photo_ids=photo_ids)
    await message.answer(f"✅ Фото {len(photo_ids)} принято. Ещё или нажмите «Готово».")


# ── Нарушитель нажал "Готово" ────────────────────────────────────────────────

@router.message(ManagerFix.waiting_photos, F.text == "✅ Готово — отправить на проверку")
async def fix_submit(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.clear()

    card_id = data["card_id"]
    fix_description = data["fix_description"]
    photo_ids: list[str] = data.get("photo_ids", [])

    await message.answer("⏳ Отправляем исправление менеджеру участка...")

    try:
        photos = []
        for file_id in photo_ids:
            file = await bot.get_file(file_id)
            file_bytes = await bot.download_file(file.file_path)
            photos.append((f"{file_id}.jpg", file_bytes.read(), "image/jpeg"))

        card = await api.bot_fix(card_id, message.from_user.id, fix_description, photos)

        await message.answer(
            f"✅ Готово! Стоп-карта #{card['id']} отправлена менеджеру участка на проверку.",
            reply_markup=await role_menu(message.from_user.id),
        )

        # Уведомляем менеджеров участка
        managers = await api.get_managers(card["section_id"])
        before_photos = [p for p in card.get("photos", []) if p.get("photo_type") == "before"]
        after_photos  = [p for p in card.get("photos", []) if p.get("photo_type") == "after"]

        for manager in managers:
            if not manager.get("telegram_id"):
                continue
            try:
                if before_photos:
                    await send_card_photos(bot, manager["telegram_id"], before_photos, "📸 Фото нарушения (ДО)")
                if after_photos:
                    await send_card_photos(bot, manager["telegram_id"], after_photos, "📸 Фото устранения (ПОСЛЕ)")
                await bot.send_message(
                    chat_id=manager["telegram_id"],
                    text=(
                        f"🧾 <b>Стоп-карта #{card['id']} — нарушитель отправил исправление</b>\n\n"
                        f"👤 Нарушитель: {card['violator_name']}\n"
                        f"📄 Нарушение: {card['description']}\n\n"
                        f"✏️ Устранение: {fix_description}\n\n"
                        f"Проверьте исправление."
                    ),
                    parse_mode="HTML",
                    reply_markup=manager_review_keyboard(card["id"]),
                )
            except Exception as e:
                logger.warning("Failed to notify manager %s: %s", manager["telegram_id"], e)

    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}", reply_markup=await role_menu(message.from_user.id))


@router.message(ManagerFix.waiting_photos)
async def fix_wrong_input(message: Message):
    await message.answer("Отправьте фото или нажмите «Готово».")


@router.callback_query(F.data.regexp(r"^(mgr_ok|mgr_return):\d+$"))
async def cb_manager_review(callback: CallbackQuery, state: FSMContext):
    action, card_id_str = callback.data.rsplit(":", 1)
    await state.set_state(ManagerReview.waiting_note)
    await state.update_data(card_id=int(card_id_str), action=action)
    if action == "mgr_ok":
        await callback.message.answer("💬 Комментарий для ОТ и ТБ (или нажмите «Пропустить»):", reply_markup=skip_keyboard())
    else:
        await callback.message.answer("💬 Укажите что нужно доработать:", reply_markup=cancel_keyboard())
    await callback.answer()


@router.message(ManagerReview.waiting_note, F.text == "➡️ Пропустить")
async def manager_review_skip(message: Message, state: FSMContext, bot: Bot):
    await _process_manager_review(message, state, bot, None)


@router.message(ManagerReview.waiting_note, F.text == "❌ Отмена")
async def manager_review_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.", reply_markup=await role_menu(message.from_user.id))


@router.message(ManagerReview.waiting_note)
async def manager_review_note(message: Message, state: FSMContext, bot: Bot):
    await _process_manager_review(message, state, bot, message.text.strip())


async def _process_manager_review(message: Message, state: FSMContext, bot: Bot, note: str | None):
    data = await state.get_data()
    await state.clear()

    card_id = data["card_id"]
    action = data["action"]

    try:
        if action == "mgr_ok":
            card = await api.manager_send_to_safety(card_id, message.from_user.id, note)
            await message.answer(
                f"✅ Стоп-карта #{card['id']} отправлена в ОТ и ТБ.",
                reply_markup=await role_menu(message.from_user.id),
            )

            engineers = await api.get_safety_engineers()
            before_photos = [p for p in card.get("photos", []) if p.get("photo_type") == "before"]
            after_photos = [p for p in card.get("photos", []) if p.get("photo_type") == "after"]
            for eng in engineers:
                if not eng.get("telegram_id"):
                    continue
                if before_photos:
                    await send_card_photos(bot, eng["telegram_id"], before_photos, "📸 Фото нарушения (ДО)")
                if after_photos:
                    await send_card_photos(bot, eng["telegram_id"], after_photos, "📸 Фото устранения (ПОСЛЕ)")
                await bot.send_message(
                    chat_id=eng["telegram_id"],
                    text=(
                        f"🔍 <b>Стоп-карта #{card['id']} — проверка ОТ и ТБ</b>\n\n"
                        f"👤 Нарушитель: {card['violator_name']}\n"
                        f"📄 Нарушение: {card['description']}\n\n"
                        f"✏️ Устранение: {card.get('fix_description') or '—'}\n"
                        f"💬 Комментарий менеджера: {note or '—'}"
                    ),
                    parse_mode="HTML",
                    reply_markup=engineer_decision_keyboard(card["id"]),
                )
        else:
            if not note:
                await message.answer("Комментарий обязателен.", reply_markup=cancel_keyboard())
                await state.set_state(ManagerReview.waiting_note)
                await state.update_data(card_id=card_id, action=action)
                return
            card = await api.manager_return(card_id, message.from_user.id, note)
            await message.answer(
                f"🔄 Стоп-карта #{card['id']} возвращена нарушителю.",
                reply_markup=await role_menu(message.from_user.id),
            )
            if card.get("violator") and card["violator"].get("id"):
                violator = await api.get_user_by_id(card["violator"]["id"])
                if violator and violator.get("telegram_id"):
                    await bot.send_message(
                        chat_id=violator["telegram_id"],
                        text=(
                            f"🔄 <b>Стоп-карта #{card['id']} возвращена на доработку</b>\n\n"
                            f"💬 Комментарий менеджера: {note}\n\n"
                            f"Исправьте нарушение и отправьте фото заново."
                        ),
                        parse_mode="HTML",
                        reply_markup=violator_accept_keyboard(card["id"]),
                    )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}", reply_markup=await role_menu(message.from_user.id))


# ── Менеджер одобряет / отклоняет нового сотрудника ──────────────────────────

@router.callback_query(F.data.startswith("uapprove:"))
async def cb_approve_user(callback: CallbackQuery, bot: Bot):
    user_id = int(callback.data.split(":")[1])
    try:
        user = await api.approve_user(user_id, callback.from_user.id)
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(f"✅ {user['full_name']} одобрен. Сотруднику отправлено уведомление.")
        await callback.answer("Одобрено")
    except Exception as e:
        await callback.answer(f"❌ {e}", show_alert=True)


@router.callback_query(F.data.startswith("ureject:"))
async def cb_reject_user(callback: CallbackQuery, bot: Bot):
    user_id = int(callback.data.split(":")[1])
    try:
        user = await api.reject_user(user_id, callback.from_user.id)
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(f"❌ {user['full_name']} отклонён.")
        await callback.answer("Отклонено")
    except Exception as e:
        await callback.answer(f"❌ {e}", show_alert=True)
