import asyncio, logging

from aiogram import Bot
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from redis.exceptions import ConnectionError

from src.crud.faq import remove_old_tickets
from src.database.redisDB import r_session
from src.database.sql_engine import Base, engine
from src import dp, token, logging_setting

async def main():
    asyncio.create_task(remove_old_tickets())
    bot = Bot(token=token)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        Base.metadata.create_all(engine)

        logging.warning("Подключение к БД успешно...")
        await r_session.ping()
        logging.warning("Подключение к РЕДИС успешно...")

    except OperationalError:
        logging.error("Не удалось подключиться к БД!")

    except ConnectionError:
        logging.error("Подключение не к РЕДИС не успешно!")

    logging.info("Бот успешно запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

# Уведомления о том что написал в тех поддержку и сделать по 1 в строчку
# Поиск в FAQ
