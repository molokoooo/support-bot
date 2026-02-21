from aiogram.fsm.state import State, StatesGroup

class FAQState(StatesGroup):
    media = State()
    title = State()
    description = State()


class FAQEditState(StatesGroup):
    media = State()
    title = State()
    description = State()
