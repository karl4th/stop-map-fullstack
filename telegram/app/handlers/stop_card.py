import asyncio
import logging
from collections import defaultdict

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputMediaPhoto, Message

logger = logging.getLogger(__name__)

_photo_locks: dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)

from app.core import api
from app.keyboards.inline import sections_keyboard
from app.keyboards.reply import cancel_keyboard, done_keyboard, main_menu, remove
from app.states.stop_card import StopCard

router = Router()

STATUS_LABELS = {
    "created":      "📋 Создана",
    "under_review": "👁 На рассмотрении",
    "in_progress":  "🔧 В работе",
    "safety_check": "🔍 Проверка ОТ и ТБ",
    "approved":     "✅ Разрешено к работе",
    "rejected":     "⛔ Запрещено",
    "closed":       "🔒 Закрыто",
}


async def _check_active(message: Message) -> bool:
    user = await api.get_user(message.from_user.id)
    if not user or user["status"] != "active":
        await message.answer("❌ У вас нет доступа. Напишите /start для регистрации.", reply_markup=remove)
        return False
    return True


@router.message(F.text == "📋 Создать стоп-карту")
async def start_stop_card(message: Message, state: FSMContext):
    if not await _check_active(message):
        return
    await state.set_state(StopCard.waiting_violator)
    await message.answer(
        "📝 Введите ФИО нарушителя:",
        reply_markup=cancel_keyboard(),
    )


@router.message(StopCard.waiting_violator)
async def got_violator(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=main_menu())
        return

    await state.update_data(violator_name=message.text.strip())
    sections = await api.get_sections()
    await state.set_state(StopCard.waiting_section)
    await message.answer("🏭 Выберите участок где произошло нарушение:", reply_markup=sections_keyboard(sections))


@router.callback_query(StopCard.waiting_section, F.data.startswith("section:"))
async def got_section(callback: CallbackQuery, state: FSMContext):
    section_id = int(callback.data.split(":")[1])
    await state.update_data(section_id=section_id)
    await state.set_state(StopCard.waiting_description)
    await callback.message.edit_reply_markup()
    await callback.message.answer(
        "📄 Опишите ситуацию (что произошло, какое нарушение):",
        reply_markup=cancel_keyboard(),
    )


@router.message(StopCard.waiting_description)
async def got_description(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=main_menu())
        return

    await state.update_data(description=message.text.strip(), photo_ids=[])
    await state.set_state(StopCard.waiting_photos)
    await message.answer(
        "📸 Отправьте фото опасного момента (можно несколько).\n"
        "Когда закончите — нажмите кнопку ниже.",
        reply_markup=done_keyboard(),
    )


@router.message(StopCard.waiting_photos, F.photo)
async def got_photo(message: Message, state: FSMContext):
    async with _photo_locks[message.from_user.id]:
        data = await state.get_data()
        photo_ids = data.get("photo_ids", [])
        photo_ids.append(message.photo[-1].file_id)
        await state.update_data(photo_ids=photo_ids)
    await message.answer(f"✅ Фото {len(photo_ids)} принято. Отправьте ещё или нажмите «Готово».")


@router.message(StopCard.waiting_photos, F.text == "✅ Готово — отправить карту")
async def submit_stop_card(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.clear()

    await message.answer("⏳ Отправляем стоп-карту...", reply_markup=remove)

    try:
        card = await api.create_stop_card(
            reporter_telegram_id=message.from_user.id,
            violator_name=data["violator_name"],
            section_id=data["section_id"],
            description=data["description"],
        )

        photo_ids: list[str] = data.get("photo_ids", [])
        if photo_ids:
            photos = []
            for file_id in photo_ids:
                file = await bot.get_file(file_id)
                file_bytes = await bot.download_file(file.file_path)
                photos.append((f"{file_id}.jpg", file_bytes.read(), "image/jpeg"))
            await api.upload_photos(card["id"], photos)

        await message.answer(
            f"✅ Стоп-карта #{card['id']} создана!\n\n"
            f"👤 Нарушитель: {data['violator_name']}\n"
            f"📄 Описание: {data['description']}\n"
            f"📸 Фото: {len(photo_ids)} шт.",
            reply_markup=main_menu(),
        )

        # Уведомляем менеджеров участка
        managers = await api.get_managers(data["section_id"])
        for manager in managers:
            try:
                await bot.send_message(
                    chat_id=manager["telegram_id"],
                    text=(
                        f"🚨 Новая стоп-карта #{card['id']}\n\n"
                        f"👤 Нарушитель: {data['violator_name']}\n"
                        f"📄 {data['description']}\n\n"
                        f"Войдите в панель управления для рассмотрения."
                    ),
                )
                if photo_ids:
                    await bot.send_media_group(
                        chat_id=manager["telegram_id"],
                        media=[InputMediaPhoto(media=fid) for fid in photo_ids],
                    )
            except Exception as notify_err:
                logger.warning(
                    "Failed to notify manager %s for card #%s: %s",
                    manager["telegram_id"], card["id"], notify_err,
                )

        # Уведомляем всех инженеров ОТ и ТБ (копия)
        engineers = await api.get_safety_engineers()
        for engineer in engineers:
            try:
                await bot.send_message(
                    chat_id=engineer["telegram_id"],
                    text=(
                        f"📋 Копия стоп-карты #{card['id']}\n\n"
                        f"👤 Нарушитель: {data['violator_name']}\n"
                        f"📄 {data['description']}\n\n"
                        f"Карта передана менеджеру участка на рассмотрение."
                    ),
                )
            except Exception as notify_err:
                logger.warning(
                    "Failed to notify safety engineer %s for card #%s: %s",
                    engineer["telegram_id"], card["id"], notify_err,
                )

    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}", reply_markup=main_menu())


@router.message(StopCard.waiting_photos)
async def wrong_photo_input(message: Message):
    await message.answer("Пожалуйста, отправьте фото или нажмите «Готово».")


@router.message(F.text == "📂 Мои стоп-карты")
async def my_cards(message: Message):
    if not await _check_active(message):
        return

    cards = await api.get_my_cards(message.from_user.id)
    if not cards:
        await message.answer("У вас пока нет стоп-карт.", reply_markup=main_menu())
        return

    lines = []
    for c in cards[:10]:
        status = STATUS_LABELS.get(c["status"], c["status"])
        date = c["created_at"][:10]
        lines.append(f"#{c['id']} | {date} | {c['violator_name']} | {status}")

    await message.answer(
        "📂 Ваши стоп-карты:\n\n" + "\n".join(lines),
        reply_markup=main_menu(),
    )
