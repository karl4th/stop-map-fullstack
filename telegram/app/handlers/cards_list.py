import logging

from aiogram import Bot, F, Router
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery

from app.core import api
from app.core.photos import send_card_photos
from app.keyboards.inline import engineer_decision_keyboard, manager_fix_keyboard, manager_new_card_keyboard

logger = logging.getLogger(__name__)
router = Router()

STATUS_LABELS = {
    "created":      "📋 Создана",
    "under_review": "👁 На рассмотрении",
    "in_progress":  "🔧 В работе",
    "safety_check": "🔍 Проверка ОТ и ТБ",
    "approved":     "✅ Разрешено",
    "rejected":     "⛔ Запрещено",
    "closed":       "🔒 Закрыто",
}


def _card_keyboard(card: dict) -> InlineKeyboardMarkup:
    status = card.get("status", "")
    cid = card["id"]
    photo_count = len(card.get("photos", []))

    rows = []

    if status == "created":
        rows.append([InlineKeyboardButton(text="✅ Принять — остановить работы", callback_data=f"ack:{cid}")])
    elif status in ("under_review", "in_progress"):
        rows.append([InlineKeyboardButton(text="📝 Описать устранение нарушения", callback_data=f"fix:{cid}")])
    elif status == "safety_check":
        rows.append([
            InlineKeyboardButton(text="✅ Разрешить", callback_data=f"se_ok:{cid}"),
            InlineKeyboardButton(text="🔄 Доработать", callback_data=f"se_fix:{cid}"),
            InlineKeyboardButton(text="⛔ Запретить", callback_data=f"se_no:{cid}"),
        ])

    if photo_count > 0:
        rows.append([InlineKeyboardButton(
            text=f"📸 Фотографии ({photo_count})",
            callback_data=f"photos:{cid}",
        )])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def _format_card(card: dict) -> str:
    status = STATUS_LABELS.get(card["status"], card["status"])
    date = card["created_at"][:10]
    desc = card["description"][:80]
    lines = [f"#{card['id']} · {date} · {status}", f"👤 {card['violator_name']}", f"📄 {desc}"]
    if card.get("fix_description"):
        lines.append(f"✏️ {card['fix_description'][:80]}")
    if card.get("safety_note") and card["status"] == "in_progress":
        lines.append(f"💬 Замечание: {card['safety_note'][:80]}")
    return "\n".join(lines)


# ── Менеджер: требуют принятия ─────────────────────────────────────────────────

@router.message(F.text == "🚨 Требуют принятия")
async def manager_need_accept(message: Message):
    await _show_manager_cards(message, statuses={"created"})


@router.message(F.text == "🔧 Требуют устранения")
async def manager_need_fix(message: Message):
    await _show_manager_cards(message, statuses={"under_review", "in_progress"})


@router.message(F.text == "📂 Все активные карты")
async def manager_all_active(message: Message):
    await _show_manager_cards(message, statuses={"created", "under_review", "in_progress", "safety_check"})


async def _show_manager_cards(message: Message, statuses: set[str]):
    try:
        all_cards = await api.get_cards_for_manager(message.from_user.id)
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
        return

    cards = [c for c in all_cards if c["status"] in statuses]

    if not cards:
        labels = " / ".join(STATUS_LABELS.get(s, s) for s in statuses)
        await message.answer(f"✅ Нет карт со статусом: {labels}")
        return

    await message.answer(f"Найдено: {len(cards)} карт(ы)")

    for card in cards[:15]:
        try:
            await message.answer(_format_card(card), reply_markup=_card_keyboard(card))
        except Exception as e:
            logger.warning("Failed to send card %s: %s", card["id"], e)

    if len(cards) > 15:
        await message.answer(f"ℹ️ Показаны первые 15 из {len(cards)} карт.")


# ── Инженер ОТ и ТБ: на проверке ───────────────────────────────────────────────

@router.message(F.text == "🔍 На проверке ОТ и ТБ")
async def engineer_on_check(message: Message):
    try:
        cards = await api.get_cards_for_engineer(message.from_user.id)
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
        return

    if not cards:
        await message.answer("✅ Нет карт на проверке. Все устранения проверены!")
        return

    await message.answer(f"🔍 Карт на проверке: {len(cards)}")

    for card in cards[:15]:
        try:
            await message.answer(_format_card(card), reply_markup=_card_keyboard(card))
        except Exception as e:
            logger.warning("Failed to send card %s: %s", card["id"], e)

    if len(cards) > 15:
        await message.answer(f"ℹ️ Показаны первые 15 из {len(cards)} карт.")


# ── Callback: показать фотографии карты ─────────────────────────────────────────

@router.callback_query(F.data.startswith("photos:"))
async def cb_show_photos(callback: CallbackQuery, bot: Bot):
    card_id = int(callback.data.split(":")[1])
    await callback.answer("⏳ Загружаем фото...")

    try:
        card = await api.get_card(card_id)
    except Exception as e:
        await callback.message.answer(f"❌ Не удалось загрузить карту: {e}")
        return

    photos = card.get("photos", [])
    before = [p for p in photos if p.get("photo_type") == "before"]
    after  = [p for p in photos if p.get("photo_type") == "after"]

    if not photos:
        await callback.message.answer("Фотографий нет.")
        return

    chat_id = callback.message.chat.id

    if before:
        await send_card_photos(bot, chat_id, before, f"📸 Нарушение — ДО (карта #{card_id})")
    if after:
        await send_card_photos(bot, chat_id, after, f"📸 Устранение — ПОСЛЕ (карта #{card_id})")
    if not before and not after:
        await callback.message.answer("Фотографий нет.")
