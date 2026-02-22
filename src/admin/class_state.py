from aiogram.fsm.state import State, StatesGroup

class AboutState(StatesGroup):
    title = State()
    link = State()
