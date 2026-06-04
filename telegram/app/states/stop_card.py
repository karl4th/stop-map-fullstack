from aiogram.fsm.state import State, StatesGroup


class StopCard(StatesGroup):
    waiting_violator = State()
    waiting_section = State()
    waiting_description = State()
    waiting_photos = State()
