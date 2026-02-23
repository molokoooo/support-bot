from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.root.command import root_menu
from . import router
from src.crud.user import check_role

@router.callback_query(F.data == "admin_panel:menu")
async def admin_panel_menu(callback: CallbackQuery):
    telegram_id = str(callback.from_user.id)
    role = await check_role(telegram_id)

    if role in ("User", "FAQ", "Support"):
        await callback.answer("❌ Не достаточно прав")
        return await root_menu(cal=callback, type="Callback")

    builder = InlineKeyboardBuilder()
    if role == "SuperAdmin":
        builder.button(text="👤 Админы", style="danger", callback_data="admin:list:all")

    builder.button(text="👥 Изменить о нас", callback_data="about:menu:edit")
    builder.button(text="⁉️ Изменить FAQ", callback_data="faq:edit")
    builder.button(text="📨 Тех. поддержка", callback_data="support:answer:menu:all:1")
    builder.button(text="◀️ Назад", callback_data="back:menu")

    if role == "Admin":
        builder.adjust(2, 1)

    if role == "SuperAdmin":
        builder.adjust(1, 2, 1)

    button = builder.as_markup()

    text = """Это админ-панел, краткая навигация:

👤 <b>Админы</b> — управление администраторами: добавление, удаление, изменение прав.
👥 <b>Изменить о нас</b> — редактирование информации раздела «О нас» в боте.
⁉️ <b>Изменить FAQ</b> — редактирование часто задаваемых вопросов: добавление, удаление, правка существующих.
📨 <b>Тех. поддержка</b> — доступ к меню технической поддержки, где можно просматривать и отвечать на обращения пользователей.
"""
    await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=button)


@router.callback_query(F.data == "faq:edit")
async def faq_edit(callback: CallbackQuery):
    telegram_id = str(callback.from_user.id)
    role = await check_role(telegram_id)

    builder = InlineKeyboardBuilder()
    builder.button(text="➕ FAQ", style="success", callback_data="faq:edit:add")
    builder.button(text="➖ FAQ", style="danger", callback_data="faq:edit:list:1")
    builder.button(text="✏️ Изменить FAQ", style="primary", callback_data="faq:edit:list:1")
    builder.button(text="️🧹 Очистить кеш", callback_data="faq:redis:clear")
    if role == "FAQ":
        builder.button(text="◀️ Назад", callback_data="back:menu")
    elif role in ("SuperAdmin", "Admin"):
        builder.button(text="◀️ Назад", callback_data="admin_panel:menu")
    builder.adjust(2, 1)

    button = builder.as_markup()

    if role == "User" or role == "Support":
        await callback.answer("❌ Не достаточно прав")
        return await root_menu(cal=callback, type="State")

    elif role == "Admin" or role == "SuperAdmin" or role == "FAQ":
        text = """
Выбери действия:
"""
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=button)
    await callback.answer()


@router.callback_query(F.data == "about:menu:edit")
async def about_edit(callback: CallbackQuery):
    telegram_id = str(callback.from_user.id)
    role = await check_role(telegram_id)

    if role in ("User", "FAQ", "Support"):
        await callback.answer("❌ Не достаточно прав")
        return await root_menu(cal=callback, type="Callback")

    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить соц. сеть", style="success", callback_data="about:add")
    builder.button(text="➖ Удалить соц. сеть", style="danger", callback_data="about:remove")
    builder.button(text="◀️ Назад", callback_data="admin_panel:menu")
    builder.adjust(2, 1)
    button = builder.as_markup()

    await callback.message.edit_text(text="Выбери действие:", parse_mode="HTML", reply_markup=button)


@router.callback_query(F.data == "about:menu:edit:state")
async def about_edit(callback: CallbackQuery, state: FSMContext):
    telegram_id = str(callback.from_user.id)
    role = await check_role(telegram_id)

    if role in ("User", "FAQ", "Support"):
        await callback.answer("❌ Не достаточно прав")
        return await root_menu(cal=callback, type="Callback")

    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить соц. сеть", style="success", callback_data="about:add")
    builder.button(text="➖ Удалить соц. сеть", style="danger", callback_data="about:remove")
    builder.button(text="◀️ Назад", callback_data="admin_panel:menu")
    builder.adjust(2, 1)
    button = builder.as_markup()

    await state.clear()
    await callback.message.edit_text(text="Выбери действие:", parse_mode="HTML", reply_markup=button)
