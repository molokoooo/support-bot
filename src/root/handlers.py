from aiogram import F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.crud.user import check_role
from src.root import router
from src.root.command import root_menu

@router.callback_query(F.data == "faq:menu")
async def faq(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()
    # ==== KEYBORD ALL ====
    builder.button(text="◀️ Назад", callback_data="back:menu")
    # BUTTON FAQ FAQ
    button = builder.as_markup()

    text = "Все ⁉️FAQ \\(часто задаваемые вопросы\\):"
    await callback.message.edit_text(text=text, parse_mode="MarkdownV2", reply_markup=button)


@router.callback_query(F.data == "about:menu")
async def about(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()
    # ==== KEYBORD ALL ====
    builder.button(text="◀️ Назад", callback_data="back:menu")
    # BUTTON ABOUT AS FOR
    button = builder.as_markup()

    text = "Все о нас:"
    await callback.message.edit_text(text=text, parse_mode="MarkdownV2", reply_markup=button)


@router.callback_query(F.data == "back:menu")
async def back(callback: CallbackQuery):
    await root_menu(cal=callback, type="Callback")

