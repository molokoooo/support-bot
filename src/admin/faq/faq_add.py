import os
from pathlib import Path

from aiogram import F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.media_group import MediaGroupBuilder

from src.root.command import root_menu
from .. import router
from src.crud.user import check_role
from src.admin.faq.class_state import FAQState
from src.database.sql_engine import get_db
from src.model.faq_model import FAQ

assets_path = os.getenv("ASSETS_PATH")

@router.callback_query(F.data == "faq:edit")
async def faq_edit(callback: CallbackQuery):
    telegram_id = str(callback.from_user.id)
    role = await check_role(telegram_id)

    builder = InlineKeyboardBuilder()
    builder.button(text="➕ FAQ", callback_data="faq:edit:add")
    builder.button(text="➖ FAQ", callback_data="faq:edit:list:1")
    builder.button(text="✏️ Изменить FAQ", callback_data="faq:edit:list:1")
    builder.button(text="️🧹 Очистить кещ", style="success", callback_data="faq:redis:clear")
    builder.button(text="◀️ Назад", callback_data="back:menu")
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


@router.callback_query(F.data == "faq:edit:add")
async def faq_edit(callback: CallbackQuery, state: FSMContext):
    telegram_id = str(callback.from_user.id)
    role = await check_role(telegram_id)
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", style="danger", callback_data="back:menu:state")
    button = builder.as_markup()

    if role == "User" or role == "Support":
        await callback.answer("❌ Не достаточно прав")
        return await root_menu(cal=callback, type="State")

    elif role == "Admin" or role == "SuperAdmin" or role == "FAQ":
        text = """
Напиши заголовок:
"""
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=button)
        await state.set_state(FAQState.title)


@router.message(FAQState.title)
async def faq_edit(message: Message, state: FSMContext):
    telegram_id = str(message.from_user.id)
    role = await check_role(telegram_id)
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", style="danger", callback_data="back:menu:state")
    button = builder.as_markup()
    await state.update_data(chat_id=message.chat.id)

    if role == "User" or role == "Support":
        await message.answer("❌ Не достаточно прав")
        return await root_menu(cal=message, type="State")

    elif role == "Admin" or role == "SuperAdmin" or role == "FAQ":
        if message.photo:
            return await message.answer("❌ Такой формат не поддерживается! Отправь текст.", reply_markup=button)
        elif message.video:
            return await message.answer("❌ Такой формат не поддерживается! Отправь текст.", reply_markup=button)
        elif message.document:
            return await message.answer("❌ Такой формат не поддерживается! Отправь текст.", reply_markup=button)
        if len(message.text) > 25:
            return await message.answer("❌Слишком много символов! Напиши до 25 символов", reply_markup=button)
        await state.update_data(title=message.text)
        text = "Напиши описание:"
        await message.answer(text, parse_mode="HTML", reply_markup=button)
        await state.set_state(FAQState.description)


@router.message(FAQState.description)
async def faq_edit(message: Message, state: FSMContext):
    telegram_id = str(message.from_user.id)
    role = await check_role(telegram_id)
    builder = InlineKeyboardBuilder()
    builder.button(text="⏩ Пропустить медиа", callback_data="faq:media:skip")
    builder.button(text="❌ Отмена", style="danger", callback_data="back:menu:state")
    builder.adjust(1)
    button = builder.as_markup()

    if role == "User" or role == "Support":
        await message.answer("❌ Не достаточно прав")
        return await root_menu(cal=message, type="State")

    elif role == "Admin" or role == "SuperAdmin" or role == "FAQ":
        if message.photo:
            return await message.answer("❌ Такой формат не поддерживается! Отправь текст.", reply_markup=button)
        elif message.video:
            return await message.answer("❌ Такой формат не поддерживается! Отправь текст.", reply_markup=button)
        elif message.document:
            return await message.answer("❌ Такой формат не поддерживается! Отправь текст.", reply_markup=button)
        if len(message.text) > 999:
            return await message.answer("❌Слишком много символов! Напиши до 999 символов", reply_markup=button)

        await state.update_data(description=message.text)
        text = "Отправь 1 изоображение или видео:"

        await message.answer(text, parse_mode="HTML", reply_markup=button)
        await state.set_state(FAQState.media)


@router.message(FAQState.media)
async def faq_edit(message: Message, state: FSMContext):
    telegram_id = str(message.from_user.id)
    role = await check_role(telegram_id)

    builder = InlineKeyboardBuilder()
    builder.button(text="⏩ Дальше", callback_data="faq:media:conf")
    builder.button(text="❌ Отмена", style="danger", callback_data="back:menu:state")
    builder.adjust(1)
    button = builder.as_markup()

    if role in ("User", "Support"):
        await message.answer("❌ Не достаточно прав")
        return await root_menu(cal=message, type="State")

    data = await state.get_data()
    media_list = data.get("media", [])
    count_media = len(media_list) + 1

    if count_media > 10:
        return await message.answer(text='Достигнут лимит! Нажмите на кнопку "⏩ Дальше" для продолжения!', reply_markup=button)

    if message.photo:
        file_id = message.photo[-1].file_id
        media_list.append({"type": "photo", "file_id": file_id})
        await state.update_data(media=media_list)
    elif message.video:
        file_id = message.video.file_id
        media_list.append({"type": "video", "file_id": file_id})
        await state.update_data(media=media_list)
    else:
        return await message.answer("❌ Такой формат не поддерживается! Отправь видео или фото.")

    text=f"""
Отправленно фото {count_media} из 10
"""

    await message.answer(text=text, parse_mode="HTML", reply_markup=button)

@router.callback_query(F.data == "faq:media:conf")
async def faq_edit(callback: CallbackQuery, state: FSMContext, bot: Bot):
    telegram_id = str(callback.from_user.id)
    role = await check_role(telegram_id)

    if role in ("User", "Support"):
        await callback.answer("❌ Не достаточно прав")
        return await root_menu(cal=callback, type="State")

    data = await state.get_data()
    media_list = data.get("media", [])
    title = data["title"]
    description = data["description"]

    text =f"""*{title}*\n\n{description}"""

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Принять", callback_data="faq:add:accept")
    builder.button(text="❌ Отклонить", callback_data="back:menu")
    builder.button(text="✏️ Изменить", callback_data="faq:media:edit")
    builder.adjust(2, 1)
    button = builder.as_markup()

    # ====== Отправка медиа ======
    if len(media_list) == 1:
        item = media_list[0]
        if item["type"] == "photo":
            await callback.message.answer_photo(
                photo=item["file_id"],
                caption=text,
                parse_mode="HTML", reply_markup=button
            )
        elif item["type"] == "video":
            await callback.message.answer_video(
                video=item["file_id"],
                caption=text,
                parse_mode="HTML", reply_markup=button
            )
    else:
        # Несколько медиа → альбом
        media_group = MediaGroupBuilder()
        for idx, item in enumerate(media_list):
            if item["type"] == "photo":
                media_group.add_photo(
                    media=item["file_id"],
                    caption=text if idx == 0 else None,
                    parse_mode="HTML" if idx == 0 else None
                )
            elif item["type"] == "video":
                media_group.add_video(
                    media=item["file_id"],
                    caption=text if idx == 0 else None,
                    parse_mode="HTML" if idx == 0 else None
                )

        await callback.bot.send_media_group(chat_id=callback.message.chat.id, media=media_group.build())

        # ====== Кнопки отдельным сообщением ======
        await callback.message.answer(text="Выберите действие:", reply_markup=button)

    await state.set_state(None)
    await callback.answer()


@router.callback_query(F.data == "faq:media:skip")
async def skip_media(callback: CallbackQuery, state: FSMContext):
    telegram_id = str(callback.from_user.id)
    data = await state.get_data()
    role = await check_role(telegram_id)
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Принять", callback_data="faq:add:accept")
    builder.button(text="❌ Отклонить", callback_data="back:menu")
    builder.button(text="✏️ Изменить", callback_data="faq:media:edit")
    builder.adjust(2, 1)
    button = builder.as_markup()

    if role == "User" or role == "Support":
        await callback.answer("❌ Не достаточно прав")
        return await root_menu(cal=callback, type="State")

    elif role == "Admin" or role == "SuperAdmin" or role == "FAQ":
        title = data.get("title", "")
        description = data.get("description", "")

        text = f"{title}\n\n{description}"
        await callback.message.answer(text, parse_mode="HTML", reply_markup=button)

    await state.set_state(None)
    await callback.answer()


@router.callback_query(F.data == "faq:add:accept")
async def accept_faq(callback: CallbackQuery, state: FSMContext):
    telegram_id = str(callback.from_user.id)
    role = await check_role(telegram_id)
    bot = callback.bot

    if role == "User" or role == "Support":
        await callback.answer("❌ Не достаточно прав")
        return await root_menu(cal=callback, type="State")

    elif role in ("Admin", "SuperAdmin", "FAQ"):
        data = await state.get_data()
        media_list = data.get("media", [])
        title = data.get("title", "")
        description = data.get("description", "")

        with get_db() as db:
            faq_new = FAQ(
                title=title,
                description=description,
                media=[]  # временно пусто
            )

            db.add(faq_new)
            db.commit()
            faq_dir = os.path.join(assets_path, str(faq_new.id))
            db.refresh(faq_new)
            os.makedirs(faq_dir, exist_ok=True)

            saved_paths = []

            faq_dir = Path(faq_dir)  # превращаем в объект Path

            for i, item in enumerate(media_list, start=1):
                file_id = item["file_id"]
                file = await bot.get_file(file_id)
                ext = Path(file.file_path).suffix
                file_path = faq_dir / f"{i}{ext}"
                file_path.parent.mkdir(parents=True, exist_ok=True)
                await bot.download_file(file.file_path, file_path)
                saved_paths.append(str(file_path))

            faq_new.media = saved_paths
            db.commit()
            db.refresh(faq_new)

        await callback.answer("✅ FAQ успешно добавлен!")

        await root_menu(cal=callback, type="CallbackAndImage")
        await state.clear()
