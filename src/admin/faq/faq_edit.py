import json
import os
from pathlib import Path

from aiogram import F, Bot
from sqlalchemy import select
from dotenv import load_dotenv
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.root.command import root_menu
from .. import router
from src.crud.user import check_role
from src.admin.faq.class_state import FAQEditState
from src.database.redisDB import r_session
from src.crud.faq import load_faq_list, load_faq_info
from src.database.sql_engine import get_db
from src.model.faq_model import FAQ

load_dotenv()
assets_path = os.getenv("ASSETS_PATH")
page_size = int(os.getenv("FAQ_PAGE_SIZE"))

@router.callback_query(F.data.startswith("faq:edit:list:"))
async def show_edit_list(callback: CallbackQuery):
    page = int(callback.data.split(":")[-1])
    telegram_id = str(callback.from_user.id)
    role = await check_role(telegram_id)

    if role in ("User", "Support"):
        await callback.answer("❌ Не достаточно прав")
        return await root_menu(cal=callback, type="State")

    button = await load_faq_list(page, "Admin")
    text="Выбери FAQ:"

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=button)


@router.callback_query(F.data.startswith("faq:list_edit:"))
async def list_edit(callback: CallbackQuery, state: FSMContext, bot: Bot):
    page = int(callback.data.split(":")[-1])
    telegram_id = str(callback.from_user.id)
    role = await check_role(telegram_id)

    if role in ("User", "Support"):
        await callback.answer("❌ Не достаточно прав")
        return await root_menu(cal=callback, type="State")

    # ==== Удаляем предыдущие сообщения FAQ, если они есть ====
    data = await state.get_data()
    faq_messages = data.get("faq_messages", [])
    for msg_id in faq_messages:
        try:
            await bot.delete_message(chat_id=callback.message.chat.id, message_id=msg_id)
        except:
            pass  # если сообщение уже удалено

    # ==== Строим клавиатуру для текущей страницы FAQ ====
    button = await load_faq_list(page, "Admin")

    text = "Выбери FAQ:"

    # ==== Отправляем новое сообщение с кнопками ====
    await callback.message.answer(text=text, parse_mode="HTML", reply_markup=button)


@router.callback_query(F.data.startswith("faq:edit-"))
async def edit_faq(callback: CallbackQuery, state: FSMContext):
    telegram_id = str(callback.from_user.id)
    role = await check_role(telegram_id)
    id = int(callback.data.split("-")[-2])
    page = int(callback.data.split("-")[-1])

    if role in ("User", "Support"):
        await callback.answer("❌ Не достаточно прав")
        return await root_menu(cal=callback, type="State")

    await load_faq_info(callback=callback, id=id, page=page, role="Admin", state=state)


@router.callback_query(F.data.startswith("faq-edit:"))
async def faq_edit_content(callback: CallbackQuery, state: FSMContext):
    id = int(callback.data.split(":")[-2])
    page = int(callback.data.split(":")[-1])
    telegram_id = str(callback.from_user.id)
    role = await check_role(telegram_id)

    if role == "User" or role == "Support":
        await callback.answer("❌ Не достаточно прав")
        return await root_menu(cal=callback, type="State")

    with get_db() as db:
        stmt = select(FAQ).where(FAQ.id == id)
        faq_obj = db.scalar(stmt)
        title = faq_obj.title
        description = faq_obj.description
        media = faq_obj.media
        await state.update_data(
            id=id,
            title=title,
            description=description,
            media=media,
            page=page
        )

    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Заголовок", callback_data=f"faq:edit:title")
    builder.button(text="✏️ Описание", callback_data=f"faq:edit:description")
    builder.button(text="🌄 Медиа", callback_data=f"faq:edit:media")
    builder.adjust(2, 1)
    button = builder.as_markup()

    await callback.message.answer("Выбери что хочешь поменять:", reply_markup=button)


@router.callback_query(F.data == "faq:edit:title")
async def faq_edit_content(callback: CallbackQuery, state: FSMContext):
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
        await state.set_state(FAQEditState.title)


@router.callback_query(F.data == "faq:edit:description")
async def faq_edit_content(callback: CallbackQuery, state: FSMContext):
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
Напиши описание:
        """
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=button)
        await state.set_state(FAQEditState.description)


@router.callback_query(F.data == "faq:edit:media")
async def faq_edit_content(callback: CallbackQuery, state: FSMContext):
    telegram_id = str(callback.from_user.id)
    role = await check_role(telegram_id)
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", style="danger", callback_data="back:menu:state")
    button = builder.as_markup()

    if role in ("User", "Support"):
        await callback.answer("❌ Не достаточно прав")
        return await root_menu(cal=callback, type="State")

    text = """
Отправь 1 изоображение или видео:
        """
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=button)
    await state.update_data(media=None)
    await state.set_state(FAQEditState.media)


@router.message(FAQEditState.title)
async def faq_edit(message: Message, state: FSMContext):
    telegram_id = str(message.from_user.id)
    role = await check_role(telegram_id)
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ В главное меню", style="success", callback_data="back:menu")
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
        if len(message.text) > 25:
            return await message.answer("❌Слишком много символов! Напиши до 25 символов", reply_markup=button)

        data = await state.get_data()
        title=message.text
        description = data["description"]
        media = data["media"]
        id = data["id"]
        page = data["page"]

        redis_key = f"faq:page:{page}"

        with get_db() as db:
            stmt = select(FAQ).where(FAQ.id == id)
            faq_entry = db.execute(stmt).scalar_one_or_none()

            if faq_entry:
                faq_entry.title = title
                faq_entry.description = description
                faq_entry.media = media
                db.commit()

                # ==== Обновляем кэш Redis ====
                stmt_all = select(FAQ).limit(page_size).offset((page - 1) * page_size)
                result = db.scalars(stmt_all).all()

                faq_list = []
                for f in result:
                    faq_list.append({
                        "id": str(f.id),
                        "title": str(f.title),
                        "description": str(f.description),
                        "media": json.dumps(f.media) if f.media else "[]"
                    })

                await r_session.set(redis_key, json.dumps(faq_list, ensure_ascii=False), ex=1800)

        text = "✅ Успешно измененно!"
        await message.answer(text, parse_mode="HTML", reply_markup=button)
        await state.clear()


@router.message(FAQEditState.description)
async def faq_edit(message: Message, state: FSMContext):
    telegram_id = str(message.from_user.id)
    role = await check_role(telegram_id)
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ В главное меню", style="success", callback_data="back:menu")
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

        data = await state.get_data()
        title = data["title"]
        description = message.text
        media = data["media"]
        id = data["id"]
        page = data["page"]

        redis_key = f"faq:page:{page}"

        with get_db() as db:
            stmt = select(FAQ).where(FAQ.id == id)
            faq_entry = db.execute(stmt).scalar_one_or_none()

            if faq_entry:
                faq_entry.title = title
                faq_entry.description = description
                faq_entry.media = media
                db.commit()

                # ==== Обновляем кэш Redis ====
                stmt_all = select(FAQ).limit(page_size).offset((page - 1) * page_size)
                result = db.scalars(stmt_all).all()

                faq_list = []
                for f in result:
                    faq_list.append({
                        "id": str(f.id),
                        "title": str(f.title),
                        "description": str(f.description),
                        "media": json.dumps(f.media) if f.media else "[]"
                    })

                await r_session.set(redis_key, json.dumps(faq_list, ensure_ascii=False), ex=1800)

        text = "✅ Успешно измененно!"

        await message.answer(text, parse_mode="HTML", reply_markup=button)
        await state.clear()


@router.message(FAQEditState.media)
async def faq_edit_media(message: Message, state: FSMContext):
    telegram_id = str(message.from_user.id)
    role = await check_role(telegram_id)

    builder = InlineKeyboardBuilder()
    builder.button(text="⏩ Дальше", callback_data="faq:edit:media:accept")
    builder.button(text="❌ Отмена", callback_data="back:menu:state")
    builder.adjust(1)
    button = builder.as_markup()

    if role in ("User", "Support"):
        await message.answer("❌ Не достаточно прав", reply_markup=button)
        return await root_menu(cal=message, type="State")

    # Определяем новый медиа-файл
    if message.photo:
        new_item = {"type": "photo", "file_id": message.photo[-1].file_id}
    elif message.video:
        new_item = {"type": "video", "file_id": message.video.file_id}
    else:
        return await message.answer(
            "❌ Такой формат не поддерживается! Отправь видео или фото.", reply_markup=button
        )

    # Получаем уже прикрепленные файлы из FSM, если None → []
    data = await state.get_data()
    media_list = data.get("media") or []

    if len(media_list) >= 10:
        return await message.answer("❌ Максимум 10 медиафайлов!", reply_markup=button)

    media_list.append(new_item)
    await state.update_data(media=media_list)

    await message.answer(
        f"📎 Медиа прикреплено ({len(media_list)}/10)! Отправьте ещё или нажмите «Дальше».",
        reply_markup=button
    )


@router.callback_query(F.data == "faq:edit:media:accept")
async def faq_edit_media_accept(callback: CallbackQuery, state: FSMContext, bot: Bot):
    telegram_id = str(callback.from_user.id)
    role = await check_role(telegram_id)

    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад в главное меню", style="success", callback_data="back:menu")
    builder.adjust(1)
    button = builder.as_markup()

    if role in ("User", "Support"):
        await callback.answer("❌ Не достаточно прав")
        return await root_menu(cal=callback, type="State")

    data = await state.get_data()
    faq_id = data.get("id")
    page = data.get("page")
    media_list = data.get("media") or []

    if not media_list:
        return await callback.message.answer(
            "❌ Медиа не найдено, отправьте файл заново.", reply_markup=button
        )

    with get_db() as db:
        stmt = select(FAQ).where(FAQ.id == faq_id)
        faq_entry = db.execute(stmt).scalar_one_or_none()

        if not faq_entry:
            return await callback.message.answer("❌ FAQ не найден!", reply_markup=button)

        # ==== Удаляем старые файлы ====
        if faq_entry.media:
            for path in faq_entry.media:
                if os.path.exists(path):
                    os.remove(path)

        # ==== Скачиваем новые файлы ====
        faq_dir = Path(assets_path) / str(faq_id)
        faq_dir.mkdir(parents=True, exist_ok=True)

        saved_paths = []
        for idx, item in enumerate(media_list, start=1):
            file = await bot.get_file(item["file_id"])
            ext = Path(file.file_path).suffix
            file_path = faq_dir / f"{idx}{ext}"
            await bot.download_file(file.file_path, file_path)
            saved_paths.append(str(file_path))

        # ==== Сохраняем новые пути в БД ====
        faq_entry.media = saved_paths
        db.commit()
        db.refresh(faq_entry)

        # ==== Обновляем кэш Redis ====
        redis_key = f"faq:page:{page}"
        stmt_all = select(FAQ).limit(page_size).offset((page - 1) * page_size)
        result = db.scalars(stmt_all).all()

        faq_list = []
        for f in result:
            faq_list.append({
                "id": str(f.id),
                "title": str(f.title),
                "description": str(f.description),
                "media": json.dumps(f.media) if f.media else "[]"
            })

        await r_session.set(redis_key, json.dumps(faq_list, ensure_ascii=False), ex=1800)

    # ==== Обновляем FSM state ====
    await state.clear()

    await callback.message.edit_text(
        f"✅ Медиа успешно обновлено! Сохранено файлов: {len(saved_paths)}",
        reply_markup=button
    )


@router.callback_query(
    F.data.startswith("faq:admin:next:") |
    F.data.startswith("faq:admin:back:")
)
async def faq_next(callback: CallbackQuery):
    page = int(callback.data.split(":")[-1])
    button = await load_faq_list(page, "Admin")
    role = await check_role(telegram_id=callback.user.id)

    if role in ("User", "Support"):
        await callback.answer("❌ Не достаточно прав")
        return await root_menu(cal=callback, type="State")

    text = f"Все FAQ СТРАНИЦА:"

    # ==== Отправляем новое сообщение с кнопками ====
    await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=button)
