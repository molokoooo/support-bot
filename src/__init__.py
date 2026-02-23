import os

from aiogram import Dispatcher
from dotenv import load_dotenv

from src.root import router as root_router
from src.admin import router as admin_router
from src.faq import router as faq_router
from src.support import router as support_router

load_dotenv()

token = os.getenv("BOT_TOKEN")

dp = Dispatcher(token=token)

dp.include_router(root_router)
dp.include_router(admin_router)
dp.include_router(faq_router)
dp.include_router(support_router)
