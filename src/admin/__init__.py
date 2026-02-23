from aiogram import Router

router = Router()

from . import admin_panel, about_as, admin_edit
from .faq import faq_add, faq_edit, faq_remove, faq_redis
from .support import answer_support
