from aiogram.fsm.state import State, StatesGroup


class EngineerDecision(StatesGroup):
    waiting_note = State()
