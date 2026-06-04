from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Contact, Message

from app.core import api
from app.keyboards.inline import sections_keyboard
from app.keyboards.reply import cancel_keyboard, main_menu, phone_keyboard, remove
from app.states.registration import Registration

router = Router()

STATUS_MSGS = {
    "pending": "⏳ Ваша заявка на рассмотрении. Ожидайте подтверждения менеджера.",
    "blocked": "🚫 Ваш аккаунт заблокирован. Обратитесь к администратору.",
}


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = await api.get_user(message.from_user.id)

    if user is None:
        await state.set_state(Registration.waiting_name)
        await message.answer(
            "👋 Добро пожаловать в систему StopMap!\n\nВведите ваше ФИО:",
            reply_markup=cancel_keyboard(),
        )
        return

    if user["status"] in STATUS_MSGS:
        await message.answer(STATUS_MSGS[user["status"]], reply_markup=remove)
        return

    await message.answer("✅ Вы авторизованы. Выберите действие:", reply_markup=main_menu())


@router.message(Registration.waiting_name)
async def got_name(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=remove)
        return

    await state.update_data(full_name=message.text.strip())
    await state.set_state(Registration.waiting_phone)
    await message.answer(
        "📱 Поделитесь вашим номером телефона:",
        reply_markup=phone_keyboard(),
    )


@router.message(Registration.waiting_phone, F.contact)
async def got_phone(message: Message, state: FSMContext):
    contact: Contact = message.contact
    if contact.user_id != message.from_user.id:
        await message.answer("Пожалуйста, поделитесь своим номером телефона.")
        return

    await state.update_data(phone=contact.phone_number)

    sections = await api.get_sections()
    if not sections:
        await message.answer("❌ Нет доступных участков. Обратитесь к администратору.", reply_markup=remove)
        await state.clear()
        return

    await state.set_state(Registration.waiting_section)
    await message.answer("🏭 Выберите ваш участок:", reply_markup=sections_keyboard(sections))


@router.message(Registration.waiting_phone)
async def wrong_phone(message: Message):
    await message.answer("Пожалуйста, нажмите кнопку для отправки номера телефона.")


@router.callback_query(Registration.waiting_section, F.data.startswith("section:"))
async def got_section(callback: CallbackQuery, state: FSMContext):
    section_id = int(callback.data.split(":")[1])
    data = await state.get_data()

    try:
        await api.register_user(
            telegram_id=callback.from_user.id,
            full_name=data["full_name"],
            phone=data["phone"],
            section_id=section_id,
        )
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка регистрации: {e}", reply_markup=remove)
        await state.clear()
        return

    await state.clear()
    await callback.message.edit_reply_markup()
    await callback.message.answer(
        "✅ Заявка отправлена!\n\nМенеджер вашего участка рассмотрит её в ближайшее время.",
        reply_markup=remove,
    )
