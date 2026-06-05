import asyncio
import logging
from collections import defaultdict

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.core import api
from app.core.photos import send_card_photos
from app.keyboards.inline import engineer_decision_keyboard, manager_fix_keyboard
from app.keyboards.reply import cancel_keyboard, fix_done_keyboard, main_menu, remove
from app.states.manager_fix import ManagerFix

logger = logging.getLogger(__name__)
router = Router()

_photo_locks: dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)


# ── Менеджер нажал "Принять" ──────────────────────────────────────────────────

@router.callback_query(F.data.startswith("ack:"))
async def cb_acknowledge(callback: CallbackQuery):
    card_id = int(callback.data.split(":")[1])
    try:
        await api.bot_acknowledge(card_id, callback.from_user.id)
        await callback.message.edit_reply_markup(reply_markup=manager_fix_keyboard(card_id))
        await callback.answer("✅ Принято! Работы приостановлены до устранения.")
    except Exception as e:
        err = str(e)
        if "уже" in err or "обработана" in err or "нельзя" in err.lower():
            await callback.answer("ℹ️ Карта уже обработана", show_alert=True)
            await callback.message.edit_reply_markup(reply_markup=None)
        else:
            await callback.answer(f"❌ {err}", show_alert=True)


# ── Менеджер нажал "Описать устранение" ───────────────────────────────────────

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


# ── Менеджер вводит описание устранения ──────────────────────────────────────

@router.message(ManagerFix.waiting_description)
async def fix_got_description(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=main_menu())
        return

    await state.update_data(fix_description=message.text.strip(), photo_ids=[])
    await state.set_state(ManagerFix.waiting_photos)
    await message.answer(
        "📸 Отправьте фото после устранения (можно несколько).\n"
        "Когда закончите — нажмите кнопку ниже.",
        reply_markup=fix_done_keyboard(),
    )


# ── Менеджер отправляет фото ──────────────────────────────────────────────────

@router.message(ManagerFix.waiting_photos, F.photo)
async def fix_got_photo(message: Message, state: FSMContext):
    async with _photo_locks[message.from_user.id]:
        data = await state.get_data()
        photo_ids = data.get("photo_ids", [])
        photo_ids.append(message.photo[-1].file_id)
        await state.update_data(photo_ids=photo_ids)
    await message.answer(f"✅ Фото {len(photo_ids)} принято. Ещё или нажмите «Готово».")


# ── Менеджер нажал "Готово" ───────────────────────────────────────────────────

@router.message(ManagerFix.waiting_photos, F.text == "✅ Готово — отправить на проверку")
async def fix_submit(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.clear()

    card_id = data["card_id"]
    fix_description = data["fix_description"]
    photo_ids: list[str] = data.get("photo_ids", [])

    await message.answer("⏳ Отправляем на проверку ОТ и ТБ...", reply_markup=remove)

    try:
        photos = []
        for file_id in photo_ids:
            file = await bot.get_file(file_id)
            file_bytes = await bot.download_file(file.file_path)
            photos.append((f"{file_id}.jpg", file_bytes.read(), "image/jpeg"))

        card = await api.bot_fix(card_id, message.from_user.id, fix_description, photos)

        await message.answer(
            f"✅ Готово! Стоп-карта #{card['id']} отправлена инженеру ОТ и ТБ на проверку.",
            reply_markup=main_menu(),
        )

        # Уведомляем всех инженеров ОТ и ТБ
        engineers = await api.get_safety_engineers()
        before_photos = [p for p in card.get("photos", []) if p.get("photo_type") == "before"]
        after_photos  = [p for p in card.get("photos", []) if p.get("photo_type") == "after"]

        for eng in engineers:
            if not eng.get("telegram_id"):
                continue
            try:
                # Фото ДО
                if before_photos:
                    await send_card_photos(bot, eng["telegram_id"], before_photos, "📸 Фото нарушения (ДО)")
                # Фото ПОСЛЕ
                if after_photos:
                    await send_card_photos(bot, eng["telegram_id"], after_photos, "📸 Фото устранения (ПОСЛЕ)")
                # Текст + кнопки
                await bot.send_message(
                    chat_id=eng["telegram_id"],
                    text=(
                        f"🔍 <b>Стоп-карта #{card['id']} — проверка устранения</b>\n\n"
                        f"👤 Нарушитель: {card['violator_name']}\n"
                        f"📄 Нарушение: {card['description']}\n\n"
                        f"✏️ Устранение: {fix_description}\n\n"
                        f"Выберите решение:"
                    ),
                    parse_mode="HTML",
                    reply_markup=engineer_decision_keyboard(card["id"]),
                )
            except Exception as e:
                logger.warning("Failed to notify engineer %s: %s", eng["telegram_id"], e)

    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}", reply_markup=main_menu())


@router.message(ManagerFix.waiting_photos)
async def fix_wrong_input(message: Message):
    await message.answer("Отправьте фото или нажмите «Готово».")
