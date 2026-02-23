import json
import os
from pathlib import Path

from aiogram import F, Bot
from pyexpat.errors import messages
from sqlalchemy import select, delete
from dotenv import load_dotenv
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.root.command import root_menu
from . import router
from src.crud.user import check_role
from src.admin.faq.class_state import FAQEditState
from src.database.redisDB import r_session
from src.crud.faq import load_faq_list, load_faq_info
from src.database.sql_engine import get_db
from src.model.about_model import About
from src.admin.class_state import AboutState


@router.callback_query(F.data == "about:add")
async def about_add(callback: CallbackQuery, state: FSMContext):
    telegram_id = str(callback.from_user.id)
    role = await check_role(telegram_id)

    if role in ("User", "FAQ", "Support"):
        await callback.answer("❌ Не достаточно прав")
        return await root_menu(cal=callback, type="Callback")

    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", style="danger", callback_data="about:menu:edit:state")
    button = builder.as_markup()

    await state.set_state(AboutState.title)
    await callback.message.edit_text(text="Напиши название соц. сети:", reply_markup=button)


@router.message(AboutState.title)
async def about_title(message: Message, state: FSMContext):
    telegram_id = str(message.from_user.id)
    role = await check_role(telegram_id)

    if role in ("User", "FAQ", "Support"):
        await message.answer("❌ Не достаточно прав")
        return await root_menu(cal=message, type="Callback")

    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", style="danger", callback_data="about:menu:edit:state")
    button = builder.as_markup()

    await state.update_data(title=message.text)
    await state.set_state(AboutState.link)
    await message.answer(text="Напиши ссылку соц. сети:", reply_markup=button)


@router.message(AboutState.link)
async def about_title(message: Message, state: FSMContext):
    telegram_id = str(message.from_user.id)
    role = await check_role(telegram_id)

    if role in ("User", "FAQ", "Support"):
        await message.answer("❌ Не достаточно прав")
        return await root_menu(cal=message, type="Callback")

    data = await state.get_data()
    title = data["title"]
    link = message.text

    builder = InlineKeyboardBuilder()
    builder.button(text=title, url=link)
    builder.button(text="✅ Подтвердить", style="success", callback_data="about:edit:accept")
    builder.button(text="❌ Отмена", style="danger", callback_data="about:menu:edit:state")
    builder.adjust(1)
    button = builder.as_markup()

    await state.update_data(title=title, link=link)
    await state.set_state(None)
    await message.answer("Верна ли кнопка?", reply_markup=button)


@router.callback_query(F.data == "about:edit:accept")
async def about_accept(callback: CallbackQuery, state: FSMContext):
    telegram_id = str(callback.from_user.id)
    role = await check_role(telegram_id)

    if role in ("User", "FAQ", "Support"):
        await callback.answer("❌ Не достаточно прав")
        return await root_menu(cal=callback, type="Callback")

    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ В главное меню", style="success", callback_data="about:menu:edit")
    button = builder.as_markup()

    data = await state.get_data()
    title = data["title"]
    link = data["link"]

    with get_db() as db:
        new_about = About(
            name=title,
            link=link,
        )
        db.add(new_about)
        db.commit()
        db.refresh(new_about)
        await r_session.hset(
            f"about:{new_about.id}",
            mapping={
                "title": title,
                "link": link
            }
        )
        await r_session.sadd("about:ids", new_about.id)
        await r_session.expire("about:ids", 1800)
        await r_session.expire(f"about:{new_about.id}", 1800)

    await callback.message.edit_text(text="✅ Успешно добавлено!", reply_markup=button)


@router.callback_query(F.data == "about:remove")
async def about_remove(callback: CallbackQuery):
    telegram_id = str(callback.from_user.id)
    role = await check_role(telegram_id)

    if role in ("User", "FAQ", "Support"):
        await callback.answer("❌ Не достаточно прав")
        return await root_menu(cal=callback, type="Callback")

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
            text=data["title"], style="danger",
            callback_data=f"about:remove-{id}"
        )

    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="about:menu:edit"))

    button = builder.as_markup()

    await callback.message.edit_text(text="Выбери какую удалить:", reply_markup=button)


@router.callback_query(F.data.startswith("about:remove-"))
async def about_remove(callback: CallbackQuery):
    id = callback.data.split("-")[-1]
    telegram_id = str(callback.from_user.id)
    role = await check_role(telegram_id)

    if role in ("User", "FAQ", "Support"):
        await callback.answer("❌ Не достаточно прав")
        return await root_menu(cal=callback, type="Callback")

    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Удалить", style="danger", callback_data=f"about:remove:accept:{id}")
    builder.button(text="◀️ Назад", callback_data="about:remove")
    builder.adjust(1)
    button = builder.as_markup()

    await callback.message.edit_text(text="Точно удалить О нас?", reply_markup=button)


@router.callback_query(F.data.startswith("about:remove:accept:"))
async def about_remove(callback: CallbackQuery):
    id = callback.data.split(":")[-1]
    telegram_id = str(callback.from_user.id)
    role = await check_role(telegram_id)

    if role in ("User", "FAQ", "Support"):
        await callback.answer("❌ Не достаточно прав")
        return await root_menu(cal=callback, type="Callback")

    with get_db() as db:
        stmt = delete(About).where(About.id == id)
        db.execute(stmt)
        db.commit()
        await r_session.srem("about:ids", id)
        await r_session.delete(f"about:{id}")

    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад в главное меню", style="success", callback_data="about:remove")
    builder.adjust(1)
    button = builder.as_markup()

    await callback.message.edit_text(text="✅ Успешно удаленно!", reply_markup=button)