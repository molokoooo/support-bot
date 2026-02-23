from aiogram.fsm.state import StatesGroup, State


class TicketState(StatesGroup):
    user_ticket = State()
    admin_ticket = State()
