from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Optional, Literal

from src.crud.user import check_role
from src.root import router

async def root_menu(
    cal, type: Literal["Command", "Callback", "State", "CallbackAndImage"], state: Optional[FSMContext] = None
):
    """
    Main menu page
    """
    telegram_id = cal.from_user.id

    builder = InlineKeyboardBuilder()
    # ==== KEYBORD ALL ====
    builder.button(text="⁉️ FAQ", callback_data="faq:menu-page:1")
    builder.button(text="👥 О нас", callback_data="about:menu")
    builder.button(text="📨 Тех. поддержка", callback_data="support:menu")

    role = await check_role(telegram_id)

    if role == ("SuperAdmin", "Admin"):
        builder.button(text="🛡 Админ меню", style="danger", callback_data="admin_panel:menu")
    elif role == "FAQ":
        builder.button(text="⁉️ Изменить FAQ", style="danger", callback_data="faq:edit")
    elif role == "Support":
        builder.button(text="📨 Ответить Тех. поддержку", style="danger", callback_data="suuport:answer:menu")

    builder.adjust(2, 1)
    button = builder.as_markup()

    text = f"Привет <code>{telegram_id}</code>, твоя роль: {role}!"

    if type == "Command":
        await cal.answer(text, parse_mode="HTML", reply_markup=button)
    elif type == "CallbackAndImage":
        await cal.message.delete()
        await cal.message.answer(text, parse_mode="HTML", reply_markup=button)
    elif type == "Callback":
        await cal.message.edit_text(text, parse_mode="HTML", reply_markup=button)
    elif type == "State":
        await state.clear()
        await cal.message.delete()
        await cal.message.answer(text, parse_mode="HTML", reply_markup=button)


@router.message(Command('start'))
async def start(message: Message):
    await root_menu(cal=message, type="Command")
