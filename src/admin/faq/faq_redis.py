import logging

from aiogram import F
from aiogram.types import CallbackQuery
from .. import router
from ...crud.user import check_role
from ...database.redisDB import r_session
from ...root.command import root_menu


@router.callback_query(F.data == "faq:redis:clear")
async def faq_edit(callback: CallbackQuery):
    telegram_id = str(callback.from_user.id)
    role = await check_role(telegram_id)

    if role == "User" or role == "Support":
        await callback.answer("❌ Не достаточно прав")
        return await root_menu(cal=callback, type="State")

    async for key in r_session.scan_iter("faq:page:*"):
        await r_session.delete(key)

    await r_session.delete("faq:total_count")

    logging.warning(f'Пользователь: {telegram_id} очистил кэш для faq')
    await callback.answer("✅ Кэш успешно очищен! Теперь все faq точно обновленны!")
