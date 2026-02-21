import json, math, mimetypes, os

from typing import Annotated
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.media_group import MediaGroupBuilder
from sqlalchemy import select, func

from src.database.redisDB import r_session
from src.database.sql_engine import get_db
from src.model.faq_model import FAQ

page_size = int(os.getenv("FAQ_PAGE_SIZE"))

def type_file(path_file):
    file = path_file.split("/")[-1]
    mime_type, _ = mimetypes.guess_type(file)

    if mime_type:
        main_type = mime_type.split("/")[0]
        return main_type
    else:
        return "ERROR"

async def load_faq_list(page: int, role: Annotated["Admin", "User"]):
    builder = InlineKeyboardBuilder()
    redis_key = f"faq:page:{page}"

    # ==== Получаем страницу из Redis ====
    page_info_redis = await r_session.get(redis_key)
    if page_info_redis:
        # Десериализуем JSON
        faq_list = json.loads(page_info_redis)
        total_count_redis = await r_session.get("faq:total_count")
        if total_count_redis:
            total_count = int(total_count_redis)
        else:
            with get_db() as db:
                total_count = db.scalar(select(func.count(FAQ.id)))
            await r_session.set("faq:total_count", total_count, ex=1800)
    else:
        # ==== Если нет в кеше — читаем из БД ====
        with get_db() as db:
            stmt = select(FAQ).limit(page_size).offset((page - 1) * page_size)
            result = db.scalars(stmt).all()
            total_count = db.scalar(select(func.count(FAQ.id)))

            # Преобразуем все поля в str и сохраняем в список словарей
            faq_list = []
            for f in result:
                faq_list.append({
                    "id": str(f.id),
                    "title": str(f.title),
                    "description": str(f.description),
                    "media": json.dumps(f.media) if f.media else "[]"
                })

            # ==== Сохраняем в Redis с TTL 30 мин ====
            await r_session.set(redis_key, json.dumps(faq_list, ensure_ascii=False), ex=1800)
            await r_session.set("faq:total_count", total_count, ex=1800)

            # ==== Строим клавиатуру ====
    if not faq_list:
        builder.button(text="Пусто 😔", callback_data="back:menu")
    else:
        for faq in faq_list:
            if role == "Admin":
                builder.button(text=faq["title"], callback_data=f"faq:edit-{faq['id']}-{page}")
            else:
                builder.button(text=faq["title"], callback_data=f"faq_id:{faq['id']}:{page}")

    total_page = max(1, math.ceil(total_count / page_size))
    next_page = page + 1
    back_page = page - 1
    if role == "User":
        if page == 1:
            builder.button(text="⬅️", callback_data=f"faq:back:{total_page}")
        else:
            builder.button(text="⬅️", callback_data=f"faq:back:{back_page}")

        builder.button(text=f"{page}/{total_page}", callback_data=f"faq:search")

        if page == total_page:
            builder.button(text="➡️", callback_data=f"faq:next:1")
        else:
            builder.button(text="➡️", callback_data=f"faq:next:{next_page}")

    elif role == "Admin":
        if page == 1:
            builder.button(text="⬅️", callback_data=f"faq:admin:back:{total_page}")
        else:
            builder.button(text="⬅️", callback_data=f"faq:admin:back:{back_page}")

        builder.button(text=f"{page}/{total_page}", callback_data=f"faq:admin:search")

        if page == total_page:
            builder.button(text="➡️", callback_data=f"faq:admin:next:1")
        else:
            builder.button(text="➡️", callback_data=f"faq:admin:next:{next_page}")

    # ==== Кнопка назад ====
    if role == "Admin":
        builder.button(text="◀️ Назад", callback_data="faq:edit")
    else:
        builder.button(text="◀️ Назад", callback_data="back:menu")

    # ==== Выравнивание клавиатуры ====
    if len(faq_list) == 4:
        builder.adjust(1, 1, 1, 1, 3, 1)

    elif len(faq_list) == 3:
        builder.adjust(1, 1, 1, 3, 1)

    elif len(faq_list) == 2:
        builder.adjust(1, 1, 3, 1)

    elif len(faq_list) == 1:
        builder.adjust(1, 3, 1)

    return builder.as_markup()

async def load_faq_info(callback, id: int, page: int, role: Annotated["Admin", "User"], state: FSMContext):
    builder = InlineKeyboardBuilder()
    redis_key = f"faq:page:{page}"

    # ==== Попытка взять страницу из Redis ====
    page_info_redis = await r_session.get(redis_key)
    if page_info_redis:
        faq_list = json.loads(page_info_redis)
    else:
        # ==== Если нет в Redis — читаем из БД и сохраняем страницу ====
        with get_db() as db:
            stmt = select(FAQ).limit(page_size).offset((page - 1) * page_size)
            result = db.scalars(stmt).all()

            faq_list = []
            for f in result:
                faq_list.append({
                    "id": str(f.id),
                    "title": str(f.title),
                    "description": str(f.description),
                    "media": json.dumps(f.media) if f.media else "[]"
                })

            # Сохраняем страницу в Redis
            await r_session.set(redis_key, json.dumps(faq_list, ensure_ascii=False), ex=1800)

    # ==== Находим нужный FAQ по id ====
    faq_info = next((f for f in faq_list if str(f["id"]) == str(id)), None)
    if not faq_info:
        await callback.answer("❌ FAQ не найден", show_alert=True)
        return

    # ==== Кнопки ====
    if role == "User":
        builder.button(text="📨 Помощь", callback_data="back:menu")
        builder.button(text="◀️ Назад", callback_data=f"faq:menu:back:{page}")
        builder.adjust(1)
    elif role == "Admin":
        builder.button(text="✏️ Изменить", style="primary", callback_data=f"faq-edit:{id}:{page}")
        builder.button(text="❌ Удалить", style="danger", callback_data=f"faq:remove:{id}:{page}")
        builder.button(text="◀️ Назад", callback_data=f"faq:list_edit:{page}")
        builder.adjust(2, 1)

    button = builder.as_markup()

    # ==== Подготовка текста ====
    text = f"<b>{faq_info['title']}</b>\n\n{faq_info['description']}"
    media_list = json.loads(faq_info["media"])

    sent_messages = []

    # ==== Отправка медиа ====
    if media_list:
        media_group = MediaGroupBuilder()
        for idx, md in enumerate(media_list):
            file_type = type_file(md)
            if file_type == "image":
                if idx == 0:
                    media_group.add_photo(media=FSInputFile(md), caption=text, parse_mode="HTML")
                else:
                    media_group.add_photo(media=FSInputFile(md))
            elif file_type == "video":
                if idx == 0:
                    media_group.add_video(media=FSInputFile(md), caption=text, parse_mode="HTML")
                else:
                    media_group.add_video(media=FSInputFile(md))

        if len(media_list) == 1:
            if type_file(media_list[0]) == "image":
                msg = await callback.message.answer_photo(
                    caption=text, photo=FSInputFile(media_list[0]),
                    reply_markup=button, parse_mode="HTML"
                )
            else:
                msg = await callback.message.answer_video(
                    caption=text, video=FSInputFile(media_list[0]),
                    reply_markup=button, parse_mode="HTML"
                )
            sent_messages.append(msg)
        else:
            msgs = await callback.message.answer_media_group(media=media_group.build())
            sent_messages.extend(msgs)
            btn_msg = await callback.message.answer(text="Выберите действие:", reply_markup=button)
            sent_messages.append(btn_msg)
    else:
        msg = await callback.message.answer(text=text, reply_markup=button, parse_mode="HTML")
        sent_messages.append(msg)

    # ==== Сохраняем ID сообщений в state для последующего удаления ====
    await state.update_data(faq_messages=[m.message_id for m in sent_messages])

    await callback.message.delete()
