import os

from aiogram import F, Bot
from dotenv import load_dotenv
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.crud.faq import load_faq_list
from src.root import router
from src.root.command import root_menu

load_dotenv()

page_size = int(os.getenv("FAQ_PAGE_SIZE"))

@router.callback_query(F.data.startswith("faq:menu-page:"))
async def faq(callback: CallbackQuery):
    page = int(callback.data.split(":")[-1])

    button = await load_faq_list(page, role="User")

    text = f"Все ⁉️FAQ (часто задаваемые вопросы):"
    await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=button)


@router.callback_query(F.data == "about:menu")
async def about(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()
    # ==== KEYBORD ALL ====
    builder.button(text="◀️ Назад", callback_data="back:menu")
    # BUTTON ABOUT AS FOR
    button = builder.as_markup()

    text = "Все о нас:"
    await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=button)


@router.callback_query(F.data == "back:menu")
async def back(callback: CallbackQuery):
    await root_menu(cal=callback, type="Callback")


@router.callback_query(F.data.startswith("faq:menu:back:"))
async def main_menu_back(callback: CallbackQuery, state: FSMContext, bot: Bot):
    page = int(callback.data.split(":")[-1])

    data = await state.get_data()
    faq_messages = data["faq_messages"]
    for msg_id in faq_messages:
        await bot.delete_message(
            chat_id=callback.message.chat.id,
            message_id=msg_id
        )

    await state.clear()

    button = await load_faq_list(page, "User")

    text = "Все ⁉️FAQ (часто задаваемые вопросы):"
    await callback.message.answer(text=text, parse_mode="HTML", reply_markup=button)


@router.callback_query(F.data == "back:menu:state")
async def main_menu_back(callback: CallbackQuery, state: FSMContext):
    await root_menu(cal=callback, type="State", state=state)


@router.callback_query(
    (F.data.startswith("faq:back:")) |
    (F.data.startswith("faq:next:"))
)
async def faq_pagination(callback: CallbackQuery):
    page = int(callback.data.split(":")[-1])
    button = await load_faq_list(page, "User")

    text = f"Все ⁉️FAQ (часто задаваемые вопросы):"

    # ==== Отправляем новое сообщение с кнопками ====
    await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=button)

