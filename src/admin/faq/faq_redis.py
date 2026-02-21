from aiogram import F
from aiogram.types import CallbackQuery
from .. import router
from ...database.redisDB import r_session


@router.callback_query(F.data == "faq:redis:clear")
async def faq_edit(callback: CallbackQuery):
    async for key in r_session.scan_iter("faq:page:*"):
        await r_session.delete(key)

    await r_session.delete("faq:total_count")

    await callback.answer("✅ Кэш успешно очищен! Теперь все faq точно обновленны!")
