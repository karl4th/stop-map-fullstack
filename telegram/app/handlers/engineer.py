import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.core import api
from app.keyboards.reply import main_menu, remove, skip_keyboard
from app.states.engineer_decision import EngineerDecision

logger = logging.getLogger(__name__)
router = Router()

_ACTIONS = {
    "se_ok":  ("approve",   "✅ Разрешить"),
    "se_fix": ("revision",  "🔄 На доработку"),
    "se_no":  ("reject",    "⛔ Запретить"),
}
_PROMPTS = {
    "se_ok":  "💬 Добавьте комментарий (или нажмите «Пропустить»):",
    "se_fix": "💬 Укажите что нужно доработать (обязательно):",
    "se_no":  "💬 Укажите причину запрета:",
}


# ── Инженер нажал одну из трёх кнопок ────────────────────────────────────────

@router.callback_query(F.data.regexp(r"^(se_ok|se_fix|se_no):\d+$"))
async def cb_engineer(callback: CallbackQuery, state: FSMContext):
    key, card_id_str = callback.data.rsplit(":", 1)
    action, label = _ACTIONS[key]

    await state.set_state(EngineerDecision.waiting_note)
    await state.update_data(card_id=int(card_id_str), action=action, action_key=key, label=label)

    prompt = _PROMPTS[key]
    kb = skip_keyboard() if key == "se_ok" else cancel_keyboard()
    await callback.message.answer(prompt, reply_markup=kb)
    await callback.answer(f"Выбрано: {label}")


# ── Инженер нажал "Пропустить" ────────────────────────────────────────────────

@router.message(EngineerDecision.waiting_note, F.text == "➡️ Пропустить")
async def engineer_skip(message: Message, state: FSMContext):
    await _process(message, state, None)


# ── Инженер нажал "Отмена" ────────────────────────────────────────────────────

@router.message(EngineerDecision.waiting_note, F.text == "❌ Отмена")
async def engineer_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.", reply_markup=remove)


# ── Инженер написал комментарий ───────────────────────────────────────────────

@router.message(EngineerDecision.waiting_note)
async def engineer_got_note(message: Message, state: FSMContext):
    await _process(message, state, message.text.strip())


# ── Общая обработка решения ───────────────────────────────────────────────────

async def _process(message: Message, state: FSMContext, note: str | None):
    data = await state.get_data()
    await state.clear()

    card_id = data["card_id"]
    action = data["action"]
    label = data["label"]

    try:
        card = await api.bot_engineer(card_id, message.from_user.id, action, note)
        note_line = f"\n💬 Комментарий: {note}" if note else ""
        await message.answer(
            f"{label}\n\n"
            f"Стоп-карта #{card['id']} обработана.{note_line}",
            reply_markup=remove,
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}", reply_markup=remove)
