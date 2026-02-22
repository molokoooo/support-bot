import os

from aiogram import F, Bot
from dotenv import load_dotenv
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from src.crud.faq import load_faq_list
from src.database.redisDB import r_session
from src.database.sql_engine import get_db
from src.model.about_model import About
from src.root import router
from src.root.command import root_menu

load_dotenv()

page_size = int(os.getenv("FAQ_PAGE_SIZE"))
name_company = os.getenv("COMPANY")

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
    ids = await r_session.smembers("about:ids")

    if not ids:
        with get_db() as db:
            result = db.scalars(select(About)).all()

            for obj in result:
                await r_session.hset(
                    f"about:{obj.id}",
                    mapping={
                        "title": obj.name,
                        "link": obj.link
                    }
                )
                await r_session.sadd("about:ids", obj.id)

            await r_session.expire("about:ids", 1800)
            ids = [str(obj.id) for obj in result]

    for id in ids:
        data = await r_session.hgetall(f"about:{id}")
        if not data:
            continue

        builder.button(
            text=data["title"], style="primary",
            url=data["link"]
        )

    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="back:menu"))

    button = builder.as_markup()

    text = f"""
<b>О нас — {name_company}</b>  

Мы — команда профессионалов, которая стремится сделать ваш опыт покупки максимально удобным и приятным.  

<i>Что мы предлагаем:</i>
- Качественные товары, которые удовлетворяют ваши потребности;  
- Надёжную доставку и прозрачные условия покупки;  
- Поддержку пользователей через 📨 Тех. поддержку и FAQ;  
- Постоянное обновление ассортимента, чтобы вы находили только лучшее.  

Наша цель — радовать каждого клиента качественными продуктами и отличным сервисом.  

Спасибо, что выбираете <b>{name_company}</b>!
"""

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

