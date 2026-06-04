from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def sections_keyboard(sections: list[dict]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=s["name"], callback_data=f"section:{s['id']}")]
            for s in sections
        ]
    )
