import asyncio, logging
from aiogram import Bot

from src.database.sql_engine import Base, engine
from src import dp, token

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def main():
    Base.metadata.create_all(engine)
    bot = Bot(token=token)
    logging.info("Bot started polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
