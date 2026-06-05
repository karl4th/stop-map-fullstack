from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Contact, Message

from app.core import api
from app.keyboards.inline import sections_keyboard
from app.keyboards.reply import (
    cancel_keyboard,
    engineer_menu,
    main_menu,
    manager_menu,
    phone_keyboard,
    remove,
)
from app.states.registration import Registration

router = Router()

STATUS_MSGS = {
    "pending": (
        "⏳ <b>Заявка на рассмотрении.</b>\n\n"
        "Менеджер вашего участка рассмотрит её в ближайшее время.\n"
        "Вы получите уведомление в этом чате когда вас одобрят."
    ),
    "blocked": "🚫 Ваш аккаунт заблокирован. Обратитесь к администратору.",
}


def _role_menu(role: str):
    if role == "manager":
        return manager_menu()
    if role == "safety_engineer":
        return engineer_menu()
    return main_menu()


def _role_greeting(role: str) -> str:
    if role == "manager":
        return "👋 Добро пожаловать!\n\nВыберите нужный раздел:"
    if role == "safety_engineer":
        return "👋 Добро пожаловать!\n\nВыберите нужный раздел:"
    return "✅ Вы авторизованы. Выберите действие:"


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
        await message.answer(STATUS_MSGS[user["status"]], parse_mode="HTML", reply_markup=remove)
        return

    role = user.get("role", "worker")
    await message.answer(_role_greeting(role), reply_markup=_role_menu(role))


@router.message(Registration.waiting_name)
async def got_name(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=remove)
        return

    await state.update_data(full_name=message.text.strip())
    await state.set_state(Registration.waiting_phone)
    await message.answer("📱 Поделитесь вашим номером телефона:", reply_markup=phone_keyboard())


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
        "✅ <b>Заявка отправлена!</b>\n\n"
        "Менеджер вашего участка рассмотрит её в ближайшее время.\n"
        "Вы получите уведомление когда вас одобрят.",
        parse_mode="HTML",
        reply_markup=remove,
    )
