import datetime
import json
import logging

from aiogram import F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, delete, update

from .. import router
from src.crud.user import check_role
from src.database.sql_engine import get_db
from src.model.user_model import Ticket
from src.root.command import root_menu
from ..class_state import TicketAnswer


@router.callback_query(F.data.startswith("support:answer:menu:"))
async def support_answer(callback: CallbackQuery):
    telegram_id = str(callback.from_user.id)
    role = await check_role(telegram_id)

    if role in ("User", "FAQ"):
        await callback.answer("❌ Не достаточно прав")
        return await root_menu(cal=callback, type="Callback")

    parts = callback.data.split(":")
    state = parts[-2] if len(parts) > 4 else parts[-1]
    page = int(parts[-1]) if len(parts) > 4 else 1

    per_page = 10
    offset = (page - 1) * per_page

    builder = InlineKeyboardBuilder()

    with get_db() as db:
        if state == "all":
            stmt = select(Ticket)
            ru_state = "Все"

        elif state == "processing":
            stmt = select(Ticket).where(Ticket.state == "processing")
            ru_state = "В процессе"

        elif state == "closed":
            stmt = select(Ticket).where(Ticket.state == "closed")
            ru_state = "Закрытые"

        elif state == "open":
            stmt = select(Ticket).where(Ticket.state == "open")
            ru_state = "Открытые"

        total = db.scalars(stmt).all()
        total_count = len(total)

        stmt = stmt.limit(per_page).offset(offset)
        result = db.scalars(stmt).all()

    if not result:
        builder.button(text="😊 Обращений нет", callback_data="admin_panel:menu")

    for idx, ticket in enumerate(result, start=offset + 1):
        if ticket.state == "closed":
            icon = "🔴"
        elif ticket.state == "processing":
            icon = "🟡"
        else:
            icon = "🟢"

        builder.button(
            text=f"{idx}. {ticket.user_telegram_id} {icon}",
            callback_data=f"support:dialogy:{ticket.id}"
        )

    # 🔁 Пагинация
    total_pages = (total_count + per_page - 1) // per_page

    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️",
                callback_data=f"support:answer:menu:{state}:{page - 1}"
            )
        )

    nav_buttons.append(
        InlineKeyboardButton(
            text=f"{page}/{total_pages}",
            callback_data="noop"
        )
    )

    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data=f"support:answer:menu:{state}:{page + 1}"
            )
        )

    builder.row(*nav_buttons)

    # Фильтры
    builder.row(*[InlineKeyboardButton(text="Все", callback_data="support:answer:menu:all",
                                       style="danger" if state == "all" else ""),
                  InlineKeyboardButton(text="Открытые", callback_data="support:answer:menu:open",
                                       style="danger" if state == "open" else ""),
                  InlineKeyboardButton(text="В процессе", callback_data="support:answer:menu:processing",
                                       style="danger" if state == "processing" else ""),
                  InlineKeyboardButton(text="Закрытые", callback_data="support:answer:menu:closed",
                                       style="danger" if state == "closed" else "")])

    if role in ("Admin", "SuperAdmin"):
        builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel:menu"))
    elif role == "Support":
        builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="back:menu"))

    button = builder.as_markup()

    text = f"{ru_state} вопросы:"

    await callback.message.edit_text(text=text, reply_markup=button)


@router.callback_query(F.data.startswith("support:answer:menu-state:"))
async def support_answer_menu(callback: CallbackQuery, state: FSMContext):
    telegram_id = str(callback.from_user.id)
    role = await check_role(telegram_id)

    if role in ("User", "FAQ"):
        await callback.answer("❌ Не достаточно прав")
        return await root_menu(cal=callback, type="Callback")

    parts = callback.data.split(":")
    state_role = parts[-3]
    ticket_id = int(parts[-2])
    page = int(parts[-1]) if len(parts) > 5 else 1

    per_page = 10
    offset = (page - 1) * per_page

    builder = InlineKeyboardBuilder()

    with get_db() as db:

        # 🔄 Сначала обновляем (если не closed)
        stmt_update = (
            update(Ticket)
            .where(
                Ticket.id == ticket_id,
                Ticket.state != "closed"
            )
            .values(state="open")
        )
        db.execute(stmt_update)
        db.commit()

        # 📋 Фильтр
        if state_role == "all":
            stmt = select(Ticket)
            ru_state = "Все"
        elif state_role == "processing":
            stmt = select(Ticket).where(Ticket.state == "processing")
            ru_state = "В процессе"
        elif state_role == "closed":
            stmt = select(Ticket).where(Ticket.state == "closed")
            ru_state = "Закрытые"
        elif state_role == "open":
            stmt = select(Ticket).where(Ticket.state == "open")
            ru_state = "Открытые"
        else:
            stmt = select(Ticket)
            ru_state = "Все"

        total = db.scalars(stmt).all()
        total_count = len(total)

        stmt = stmt.limit(per_page).offset(offset)
        result = db.scalars(stmt).all()

    # 📌 Кнопки тикетов
    if not result:
        builder.button(text="😊 Обращений нет", callback_data="admin_panel:menu")
    else:
        for idx, ticket_obj in enumerate(result, start=offset + 1):
            if ticket_obj.state == "closed":
                icon = "🔴"
            elif ticket_obj.state == "processing":
                icon = "🟡"
            else:
                icon = "🟢"

            builder.button(
                text=f"{idx}. {ticket_obj.user_telegram_id} {icon}",
                callback_data=f"support:dialogy:{ticket_obj.id}"
            )

    # 🔁 Пагинация
    total_pages = (total_count + per_page - 1) // per_page

    nav_buttons = []

    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️",
                callback_data=f"support:answer:menu-state:{state_role}:{ticket_id}:{page - 1}"
            )
        )

    nav_buttons.append(
        InlineKeyboardButton(
            text=f"{page}/{total_pages}",
            callback_data="noop"
        )
    )

    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data=f"support:answer:menu-state:{state_role}:{ticket_id}:{page + 1}"
            )
        )

    builder.row(*nav_buttons)

    # 📂 Фильтры
    builder.row(*[InlineKeyboardButton(text="Все", callback_data="support:answer:menu:all",
                                       style="danger" if state == "all" else ""),
                  InlineKeyboardButton(text="Открытые", callback_data="support:answer:menu:open",
                                       style="danger" if state == "open" else ""),
                  InlineKeyboardButton(text="В процессе", callback_data="support:answer:menu:processing",
                                       style="danger" if state == "processing" else ""),
                  InlineKeyboardButton(text="Закрытые", callback_data="support:answer:menu:closed",
                                       style="danger" if state == "closed" else "")])

    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel:menu")
    )

    button = builder.as_markup()
    text = f"{ru_state} вопросы:"

    await state.clear()

    try:
        await callback.message.edit_text(text=text, reply_markup=button)
    except TelegramBadRequest:
        await callback.message.answer(text=text, reply_markup=button)


@router.callback_query(F.data.startswith("support:dialogy:"))
async def support_answer_dialog(callback: CallbackQuery, bot: Bot):
    id = int(callback.data.split(":")[-1])
    telegram_id = str(callback.from_user.id)
    chat_id = callback.message.chat.id
    role = await check_role(telegram_id)

    if role in ("User", "FAQ"):
        await callback.answer("❌ Не достаточно прав")
        return await root_menu(cal=callback, type="Callback")

    with get_db() as db:
        stmt = select(Ticket).where(Ticket.id == id)
        tickets = db.scalars(stmt).all()
        if not tickets:
            await callback.message.answer("Ошибка 404, сообщение бито, возможно пользователь заблокировал бота 😔")
            db.execute(delete(Ticket).where(Ticket.id == id))
            db.commit()
            return

        ticket = tickets[0]

        # Обработка сообщений пользователя
        message_ids = ticket.user_message_id
        if isinstance(message_ids, str):
            try:
                message_ids = json.loads(message_ids)
            except json.JSONDecodeError:
                message_ids = []

        for message_id in message_ids:
            try:
                await bot.forward_message(
                    chat_id=chat_id,
                    from_chat_id=ticket.user_telegram_id,
                    message_id=message_id
                )
            except TelegramBadRequest:
                await callback.message.answer(
                    "Ошибка 404, сообщение бито, возможно пользователь заблокировал бота 😔"
                )
                db.execute(delete(Ticket).where(Ticket.id == id))
                db.commit()
                return

        await callback.message.answer(f"Ответ модерации:\n{ticket.admin_message or 'нету'}")

        # Обновление состояния тикета
        stmt = update(Ticket).where(Ticket.id == id, Ticket.state != "closed").values(state="processing")
        db.execute(stmt)
        db.commit()

    # Построение меню действий
    builder = InlineKeyboardBuilder()
    builder.button(text="🔒 Закрыть обращение", callback_data=f"support:close:{id}")
    builder.button(text="📨 Ответить", callback_data=f"support:answer:{id}")
    builder.button(text="◀️ Назад", callback_data=f"support:answer:menu-state:all:{id}:1")
    builder.adjust(2, 1)
    button = builder.as_markup()

    logging.warning(f'Пользователь: {telegram_id} рассматривает вопрос {id}')
    await callback.message.answer("Выбери действие:", reply_markup=button)
    await callback.answer()


@router.callback_query(F.data.startswith("support:close:"))
async def close_ticket(callback: CallbackQuery):
    ticket_id = int(callback.data.split(":")[-1])
    telegram_id = str(callback.from_user.id)
    role = await check_role(telegram_id)

    if role in ("User", "FAQ"):
        await callback.answer("❌ Не достаточно прав")
        return await root_menu(cal=callback, type="Callback")

    with get_db() as db:
        stmt = update(Ticket).where(Ticket.id == ticket_id).values(state="closed",
                                                                   close_date=datetime.datetime.utcnow())
        db.execute(stmt)
        db.commit()

    logging.warning(f'Пользователь: {telegram_id} закрыл вопрос {ticket_id}')
    await callback.answer("✅ Обращение закрыто")
    await root_menu(callback, "Callback")


@router.callback_query(F.data.startswith("support:answer:"))
async def answer_ticket(callback: CallbackQuery, state: FSMContext):
    ticket_id = int(callback.data.split(":")[-1])
    telegram_id = str(callback.from_user.id)
    role = await check_role(telegram_id)

    if role in ("User", "FAQ"):
        await callback.answer("❌ Не достаточно прав")
        return await root_menu(cal=callback, type="Callback")

    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data=f"support:answer:menu-state:{ticket_id}")
    button = builder.as_markup()

    logging.warning(f'Пользователь: {telegram_id} отвечает на вопрос: {ticket_id}')
    await callback.message.edit_text("✏️ Введите ответ на обращение:", reply_markup=button)
    await state.update_data(ticket_id=ticket_id)
    await state.set_state(TicketAnswer.waiting_for_answer)
    await callback.answer()


@router.message(TicketAnswer.waiting_for_answer)
async def receive_ticket_answer(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    ticket_id = data.get("ticket_id")
    message_id = message.message_id
    telegram_id = str(message.from_user.id)
    role = await check_role(telegram_id)

    if role in ("User", "FAQ"):
        await message.answer("❌ Не достаточно прав")
        return await root_menu(cal=message, type="Command")

    if not ticket_id:
        await message.answer("❌ Ошибка: тикет не найден.")
        await state.clear()
        return

    with get_db() as db:
        # Сохраняем ответ модератора
        stmt = select(Ticket).where(Ticket.id == ticket_id)
        ticket = db.execute(stmt).scalar_one()

        new_message_text = (ticket.admin_message or "") + "\n" + message.text

        stmt_update = (
            update(Ticket)
            .where(Ticket.id == ticket_id)
            .values(admin_message=new_message_text, state="open")
        )
        db.execute(stmt_update)
        db.commit()

        # Получаем тикет с user_telegram_id и message_id
        stmt_select = select(Ticket).where(Ticket.id == ticket_id)
        ticket = db.scalars(stmt_select).first()

    if ticket:
        try:
             await bot.copy_message(
                 chat_id=ticket.user_telegram_id,
                 from_chat_id=message.chat.id,
                 message_id=message_id
             )
        except Exception as e:
                # Если пользователь заблокировал бота, просто игнорируем
            await message.answer(f"⚠️ Не удалось отправить пользователю {ticket.user_telegram_id}: {e}")

    logging.warning(f'Пользователь: {telegram_id} ответил на вопрос {ticket_id}')
    await message.answer("✅ Ответ отправлен пользователю.")
    await root_menu(message, "Command")
    await state.clear()

