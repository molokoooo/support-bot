from aiogram import Router

router = Router()

from . import admin_panel, support_answer
from .faq import faq_add, faq_edit, faq_remove, faq_redis
