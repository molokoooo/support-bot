import os

from aiogram import Dispatcher
from dotenv import load_dotenv

from src.root import router as root_router

load_dotenv()

token = os.getenv("BOT_TOKEN")

dp = Dispatcher(token=token)

dp.include_router(root_router)
