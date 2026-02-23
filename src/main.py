import asyncio, logging

from aiogram import Bot
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from redis.exceptions import ConnectionError

from src.crud.faq import remove_old_tickets
from src.database.redisDB import r_session
from src.database.sql_engine import Base, engine
from src import dp, token

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def main():
    asyncio.create_task(remove_old_tickets())
    bot = Bot(token=token)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        Base.metadata.create_all(engine)

        logging.info("Подключение к БД успешно...")
        await r_session.ping()
        logging.info("Подключение к РЕДИС успешно...")

    except OperationalError:
        logging.error("Не удалось подключиться к БД!")

    except ConnectionError:
        logging.info("Подключение не к РЕДИС не успешно!")

    logging.info("Бот успешно запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
