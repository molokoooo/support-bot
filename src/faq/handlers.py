from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from src.crud.faq import load_faq_info
from src.faq import router


@router.callback_query(F.data.startswith("faq_id:"))
async def faq(callback: CallbackQuery, state: FSMContext):
    id = int(callback.data.split(":")[-2])
    page = int(callback.data.split(":")[-1])

    await load_faq_info(callback=callback, id=id, page=page, role="User", state=state)



