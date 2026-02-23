import json, os, shutil
import logging

from pathlib import Path
from aiogram import F, Bot
from sqlalchemy import select, delete
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from src.root.command import root_menu
from .. import router
from src.crud.user import check_role
from src.database.redisDB import r_session
from src.crud.faq import load_faq_list
from src.database.sql_engine import get_db
from src.model.faq_model import FAQ

assets_path = os.getenv("ASSETS_PATH")

@router.callback_query(F.data.startswith("faq:remove:"))
async def remove_faq(callback: CallbackQuery, state: FSMContext, bot: Bot):
    telegram_id = str(callback.from_user.id)
    role = await check_role(telegram_id)
    page = int(callback.data.split(":")[-1])

    # Получаем id FAQ
    id = int(callback.data.split(":")[-2])  # faq:remove:{id}

    if role in ("User", "Support"):
        await callback.answer("❌ Не достаточно прав")
        return await root_menu(cal=callback, type="State")

    # ==== Удаляем предыдущие сообщения FAQ, если есть ====
    data = await state.get_data()
    faq_messages = data.get("faq_messages", [])
    for msg_id in faq_messages:
        try:
            await bot.delete_message(chat_id=callback.message.chat.id, message_id=msg_id)
        except:
            pass

    # ==== Удаляем сам FAQ из базы ====
    with get_db() as db:
        # Сначала получаем объект, чтобы узнать путь к папке
        stmt = select(FAQ).where(FAQ.id == id)
        faq_obj = db.scalar(stmt)

        if faq_obj:
            # Удаляем папку с медиа
            faq_dir = Path(assets_path) / str(faq_obj.id)
            if faq_dir.exists() and faq_dir.is_dir():
                shutil.rmtree(faq_dir)

            # Удаляем запись из базы
            db.execute(delete(FAQ).where(FAQ.id == id))
            db.commit()
            keys = await r_session.keys("faq:page:*")
            for key in keys:
                page_data = await r_session.get(key)
                if not page_data:
                    continue
                faq_list = json.loads(page_data)
                # Удаляем FAQ с нужным id
                new_faq_list = [f for f in faq_list if str(f["id"]) != str(id)]
                if new_faq_list:
                    # Сохраняем обновлённый список обратно в Redis
                    await r_session.set(key, json.dumps(new_faq_list, ensure_ascii=False), ex=1800)
                else:
                    # Если после удаления ничего не осталось, удаляем ключ
                    await r_session.delete(key)

    button = await load_faq_list(page, "Admin")

    logging.warning(f'Пользователь: {telegram_id} удалил faq: {faq_obj.title}')
    text = "Выбери FAQ:"
    await callback.answer(f"✅ FAQ {id} успешно удалён!")
    await callback.message.answer(text=text, parse_mode="HTML", reply_markup=button)
