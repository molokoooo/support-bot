from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Annotated

from src.crud.user import check_role
from src.root import router

async def root_menu(cal, type: str | Annotated["Command", "Callback"]):
    """
    Main menu page
    """
    telegram_id = cal.from_user.id

    builder = InlineKeyboardBuilder()
    # ==== KEYBORD ALL ====
    builder.button(text="⁉️ FAQ", callback_data="faq:menu")
    builder.button(text="👥 О нас", callback_data="about:menu")
    builder.button(text="📨 Тех. поддержка", callback_data="support:menu")

    role = await check_role(telegram_id)

    if role == "SuperAdmin":
        builder.button(text="🛡 Админ меню", callback_data="admin_panel:menu")
    elif role == "Admin":
        builder.button(text="🛡 Админ меню", callback_data="admin_panel:menu")
    elif role == "FAQ":
        builder.button(text="⁉️ Изменить FAQ", callback_data="faq:edit")
    elif role == "Support":
        builder.button(text="📨 Ответить Тех. поддержку", callback_data="suuport:answer:menu")

    builder.adjust(2, 1)
    button = builder.as_markup()

    if type == "Command":
        await cal.answer(f"Привет `{telegram_id}`, твоя роль\: {role}\!", parse_mode="MarkdownV2", reply_markup=button)
    elif type == "Callback":
        await cal.message.edit_text(f"Привет `{telegram_id}`, твоя роль\: {role}\!", parse_mode="MarkdownV2", reply_markup=button)

@router.message(Command('start'))
async def start(message: Message):
    await root_menu(cal=message, type="Command")
