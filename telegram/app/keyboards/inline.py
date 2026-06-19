from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def sections_keyboard(sections: list[dict]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=s["name"], callback_data=f"section:{s['id']}")]
            for s in sections
        ]
    )


def manager_new_card_keyboard(card_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="📋 Открыть карту", callback_data=f"photos:{card_id}"),
    ]])


def manager_review_keyboard(card_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отправить в ОТ и ТБ", callback_data=f"mgr_ok:{card_id}")],
        [InlineKeyboardButton(text="🔄 Вернуть нарушителю", callback_data=f"mgr_return:{card_id}")],
    ])


def user_approval_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Одобрить", callback_data=f"uapprove:{user_id}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"ureject:{user_id}"),
    ]])


def violator_accept_keyboard(card_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Принять и исправить", callback_data=f"ack:{card_id}"),
    ], [
        InlineKeyboardButton(text="📸 Отправить исправление", callback_data=f"fix:{card_id}"),
    ]])


def engineer_decision_keyboard(card_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Разрешить", callback_data=f"se_ok:{card_id}"),
        InlineKeyboardButton(text="🔄 Доработать", callback_data=f"se_fix:{card_id}"),
        InlineKeyboardButton(text="⛔ Запретить", callback_data=f"se_no:{card_id}"),
    ]])
