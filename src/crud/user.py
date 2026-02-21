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

def escape_markdown_v2(text: str) -> str:
    """
    Экранирует все специальные символы для MarkdownV2 в Telegram.

    Args:
        text (str): Исходный текст.

    Returns:
        str: Текст с экранированными символами.
    """
    # Все символы, которые нужно экранировать в MarkdownV2
    # \ _ * [ ] ( ) ~ ` > # + - = | { } . !
    escape_chars = r'[_*\[\]()~`>#+-=|{}.!\\]'
    return re.sub(escape_chars, lambda match: f"\\{match.group(0)}", text)
