import re

from sqlalchemy import select

from src.database.redisDB import r_session
from src.database.sql_engine import get_db
from src.model.user_model import User


async def check_role(telegram_id: str):
    """
    Получает роль пользователя по его Telegram ID.

    Сначала пытается получить роль из Redis (кэш).
    Если ключа нет или он пустой, функция обращается к базе данных:
      - Если пользователь найден, берёт его роль.
      - Если пользователь не найден, создаёт нового пользователя с заданным Telegram ID.

    После получения роли, она сохраняется в Redis с TTL 24 часа для ускорения последующих запросов.
    """
    role = await r_session.get(f"user_role:{telegram_id}")
    if not role:
        with get_db() as db:
            user = db.scalar(select(User).where(User.telegram_id == str(telegram_id)))
            if not user:
                user = User(telegram_id=str(telegram_id))
                db.add(user)
                db.commit()
                db.refresh(user)
            role = user.role

            await r_session.set(f"user_role:{telegram_id}", role, ex=60*60*24)

    return role

def markdownv2_to_html(text: str) -> str:
    # Сначала убираем экранирование MarkdownV2
    text = text.replace(r'\*', '*').replace(r'\_', '_').replace(r'\~', '~').replace(r'\`', '`').replace(r'\\', '\\')

    # Ссылки: [текст](URL) -> <a href="URL">текст</a>
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)

    # Жирный: *текст* -> <b>текст</b>
    text = re.sub(r'\*(.+?)\*', r'<b>\1</b>', text)

    # Курсив: _текст_ -> <i>текст</i>
    text = re.sub(r'\_(.+?)\_', r'<i>\1</i>', text)

    # Зачеркнутый: ~текст~ -> <s>текст</s>
    text = re.sub(r'\~(.+?)\~', r'<s>\1</s>', text)

    # Моноширинный: `текст` -> <code>текст</code>
    text = re.sub(r'\`(.+?)\`', r'<code>\1</code>', text)

    return text