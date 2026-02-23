from aiogram.fsm.state import State, StatesGroup

class AboutState(StatesGroup):
    title = State()
    link = State()

class AdminState(StatesGroup):
    telegram_id = State()

class TicketAnswer(StatesGroup):
    waiting_for_answer = State()
