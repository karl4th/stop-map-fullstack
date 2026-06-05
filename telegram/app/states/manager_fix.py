from aiogram.fsm.state import State, StatesGroup


class ManagerFix(StatesGroup):
    waiting_description = State()
    waiting_photos = State()
