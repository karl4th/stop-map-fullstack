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
        InlineKeyboardButton(text="✅ Принять — остановить работы", callback_data=f"ack:{card_id}"),
    ]])


def manager_fix_keyboard(card_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="📝 Описать устранение нарушения", callback_data=f"fix:{card_id}"),
    ]])


def engineer_decision_keyboard(card_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Разрешить", callback_data=f"se_ok:{card_id}"),
        InlineKeyboardButton(text="🔄 Доработать", callback_data=f"se_fix:{card_id}"),
        InlineKeyboardButton(text="⛔ Запретить", callback_data=f"se_no:{card_id}"),
    ]])
