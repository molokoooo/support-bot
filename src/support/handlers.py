import os

from aiogram import F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, update

from . import router
from src.database.sql_engine import get_db
from .classes import TicketState
from ..model.user_model import Ticket

company_name = os.getenv("COMPANY")

@router.callback_query(F.data == "support")
async def support_callback(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data=f"back:menu:state")
    button = builder.as_markup()
    text =f"""
📨 Приветствую это поддержка компании <b>{company_name}</b>! Задавайте ваш вопрос:
"""

    try:
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML", reply_markup= button
        )
        await state.set_state(TicketState.user_ticket)
    except TelegramBadRequest:
        pass


@router.message(TicketState.user_ticket)
async def ticket_callback(message: Message, state: FSMContext):
    message_id = message.message_id
    telegram_id = str(message.from_user.id)

    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ В главное меню", callback_data=f"back:menu")
    button = builder.as_markup()

    with get_db() as db:
        stmt = select(Ticket).where(Ticket.user_telegram_id == telegram_id)
        result = db.scalar(stmt)
        if not result:
            result = Ticket(
                user_message_id=[message_id],
                user_telegram_id=telegram_id
            )
            db.add(result)
            db.commit()
            db.refresh(result)
        else:
            message_list = result.user_message_id + [message_id]

            db.execute(
                update(Ticket)
                .where(Ticket.user_telegram_id == telegram_id)
                .values(user_message_id=message_list, state="open", close_date=None)
            )
            db.commit()

    text = f"""
<b>Ваше сообщение находится на модерации ✅</b>

Спасибо за Ваше обращение.  
Наши модераторы проверят сообщение и свяжутся с Вами при необходимости предоставления дополнительной информации.

<i>Пожалуйста, ожидайте ответа.</i>  
<b>Обращаем внимание: не удаляйте сообщения и не блокируйте бота, иначе вы не сможете получить ответ.</b>
"""

    await state.clear()
    await message.answer(text=text, parse_mode="HTML", reply_markup=button)

