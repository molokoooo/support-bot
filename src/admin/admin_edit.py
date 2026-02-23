import logging

from aiogram import F, Bot
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, update, or_

from src.root.command import root_menu
from . import router
from src.crud.user import check_role
from .class_state import AdminState
from ..database.redisDB import r_session
from ..database.sql_engine import get_db
from ..model.user_model import User


def get_role_icon(role: str) -> str:
    return "⁉️" if role == "FAQ" else "📨" if role == "Support" else "🛡"


@router.callback_query(F.data.startswith("admin:list:"))
async def admin_list(callback: CallbackQuery):
    parts = callback.data.split(":")
    role_check = parts[2] if len(parts) > 2 else "all"
    page = int(parts[3]) if len(parts) > 3 else 1

    telegram_id = str(callback.from_user.id)
    user_role = await check_role(telegram_id)

    if user_role in ("User", "FAQ", "Support", "Admin"):
        await callback.answer("❌ Не достаточно прав")
        return await root_menu(cal=callback, type="Callback")

    builder = InlineKeyboardBuilder()
    with get_db() as db:
        stmt = select(User).where(User.role != "User") if role_check == "all" else select(User).where(User.role == role_check)
        result = db.scalars(stmt).all()

    total_pages = 1
    if not result:
        builder.button(text="😔 Пусто", callback_data=f"admin_panel:menu")
    else:
        per_page = 10
        total_pages = (len(result) + per_page - 1) // per_page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_users = result[start_idx:end_idx]

        number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

        for idx, user in enumerate(page_users):
            number = number_emojis[idx] if idx < len(number_emojis) else str(idx + 1)
            builder.button(
                text=f"{number} {user.username} ({user.telegram_id})",
                callback_data=f"admin:edit:{user.id}"
            )

        builder.adjust(1)

        nav_buttons = []
        if page > 1:
            nav_buttons.append(InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=f"admin:list:{role_check}:{page-1}"
            ))
        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton(
                text="▶️ Вперед",
                callback_data=f"admin:list:{role_check}:{page+1}"
            ))
        if nav_buttons:
            builder.row(*nav_buttons)

    role_buttons = [
        InlineKeyboardButton(text="Все", callback_data=f"admin:list:all:1", style="danger" if role_check=="all" else None),
        InlineKeyboardButton(text="FAQ", callback_data=f"admin:list:FAQ:1", style="danger" if role_check=="FAQ" else None),
        InlineKeyboardButton(text="Support", callback_data=f"admin:list:Support:1", style="danger" if role_check=="Support" else None),
        InlineKeyboardButton(text="Admin", callback_data=f"admin:list:Admin:1", style="danger" if role_check=="Admin" else None),
        InlineKeyboardButton(text="SuperAdmin", callback_data=f"admin:list:SuperAdmin:1", style="danger" if role_check=="SuperAdmin" else None),
    ]
    builder.row(*role_buttons)
    builder.row(
        InlineKeyboardButton(text="➕ Добавить", style="success", callback_data="admin_add_search_remove"),
        InlineKeyboardButton(text="🔎 Поиск по ID", style="primary", callback_data="admin_add_search_remove"),
        InlineKeyboardButton(text="➖ Удалить", style="success", callback_data="admin_add_search_remove")
    )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel:menu"))

    role_display = {
        "FAQ": "⁉️ FAQ",
        "all": "👥 Все",
        "Support": "📨 Поддержка",
        "Admin": "🛡 Админы",
        "SuperAdmin": "🛡 Владельцы"
    }.get(role_check, "🛡 Владельцы")

    logging.warning(f'Пользователь: {telegram_id} смотрит список админов')
    await callback.message.edit_text(text=f"{role_display} админы — страница {page}/{total_pages}:", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("admin:edit:"))
async def admin_edit(callback: CallbackQuery):
    id = int(callback.data.split(":")[-1])
    telegram_id = str(callback.from_user.id)
    user_role = await check_role(telegram_id)

    if user_role in ("User", "FAQ", "Support", "Admin"):
        await callback.answer("❌ Не достаточно прав")
        return await root_menu(cal=callback, type="Callback")

    with get_db() as db:
        stmt = select(User).where(User.id == id)
        result = db.scalar(stmt)
        if not result:
            return await callback.answer("❌ Не удалось открыть!")

    icon = get_role_icon(result.role)
    text = f"👤 Пользователь @{result.username} ({result.telegram_id})\n{icon}Роль: {result.role}"

    builder = InlineKeyboardBuilder()
    roles = ["User", "FAQ", "Support", "Admin", "SuperAdmin"]
    buttons = [
        InlineKeyboardButton(text=r, callback_data=f"admin:role:set:{id}:{r}",
                             style="danger" if result.role == r else None)
        for r in roles
    ]
    builder.row(*buttons)
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data=f"admin:list:all"))
    await callback.message.edit_text(text=text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("admin:role:set"))
async def admin_set_role(callback: CallbackQuery):
    id = callback.data.split(":")[-2]
    role = callback.data.split(":")[-1]
    telegram_id = str(callback.from_user.id)
    user_role = await check_role(telegram_id)

    if user_role in ("User", "FAQ", "Support", "Admin"):
        await callback.answer("❌ Не достаточно прав")
        return await root_menu(cal=callback, type="Callback")

    with get_db() as db:
        # пытаемся сначала по telegram_id, если не число, по username
        try:
            id_int = int(id)
            stmt = update(User).where(User.id == id_int).values(role=role)
            db.execute(stmt)
            db.commit()
            stmt = select(User).where(User.id == id_int)
        except ValueError:
            stmt = update(User).where(User.username == id).values(role=role)
            db.execute(stmt)
            db.commit()
            stmt = select(User).where(User.username == id)

        result = db.scalar(stmt)
        await r_session.set(f"user_role:{result.telegram_id}", result.role)
        await r_session.expire(f"user_role:{result.telegram_id}", 1800)

    if not result:
        return await callback.answer("❌ Пользователь не найден!")

    icon = get_role_icon(result.role)
    text = f"👤 Пользователь @{result.username} ({result.telegram_id})\n{icon}Роль: {result.role}"

    builder = InlineKeyboardBuilder()
    roles = ["User", "FAQ", "Support", "Admin", "SuperAdmin"]
    buttons = [
        InlineKeyboardButton(text=r, callback_data=f"admin:role:set:{id}:{r}",
                             style="danger" if result.role == r else None)
        for r in roles
    ]
    builder.row(*buttons)
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data=f"admin:list:all"))
    logging.warning(f'Пользователь: {telegram_id} поменял пользователю {result.username} роль на {role}')
    await callback.message.edit_text(text=text, reply_markup=builder.as_markup())


@router.callback_query(F.data == "admin_add_search_remove")
async def admin_add_search_remove(callback: CallbackQuery, state: FSMContext):
    telegram_id = str(callback.from_user.id)
    user_role = await check_role(telegram_id)

    if user_role in ("User", "FAQ", "Support", "Admin"):
        await callback.answer("❌ Не достаточно прав")
        return await root_menu(cal=callback, type="Callback")

    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", style="danger", callback_data=f"back:menu:state")
    await state.set_state(AdminState.telegram_id)
    await callback.message.edit_text(
        text="<b>Напишите ID или username(без @) пользователя</b>\n\n"
             "<i>⚠️ Внимание! Если пользователь не запускал бота, добавить его в админы не получится.</i>",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


@router.message(AdminState.telegram_id)
async def admin_message(message: Message, state: FSMContext):
    id = message.text.strip()
    telegram_id = str(message.from_user.id)
    user_role = await check_role(telegram_id)

    if user_role in ("User", "FAQ", "Support", "Admin"):
        await message.answer("❌ Не достаточно прав")
        return await root_menu(cal=message, type="State")

    with get_db() as db:
        try:
            id_int = int(id)
            stmt = select(User).where(User.telegram_id == id_int)
            result = db.scalar(stmt)
        except ValueError:
            stmt = select(User).where(User.username == id)
            result = db.scalar(stmt)

        if not result:
            builder = InlineKeyboardBuilder()
            builder.button(text="❌ Отмена", style="danger", callback_data=f"back:menu:state")
            return await message.answer("❌ Такого пользователя нет!", reply_markup=builder.as_markup())

    icon = get_role_icon(result.role)
    text = f"👤 Пользователь @{result.username} ({result.telegram_id})\n{icon}Роль: {result.role}"

    builder = InlineKeyboardBuilder()
    roles = ["User", "FAQ", "Support", "Admin", "SuperAdmin"]
    buttons = [
        InlineKeyboardButton(text=r, callback_data=f"admin:role:set:{id}:{r}",
                             style="danger" if result.role == r else None)
        for r in roles
    ]
    builder.row(*buttons)
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data=f"admin:list:all"))

    logging.warning(f'Пользователь: {telegram_id} нашёл пользователя {result.username}')
    await message.answer(text=text, reply_markup=builder.as_markup())
    await state.clear()
