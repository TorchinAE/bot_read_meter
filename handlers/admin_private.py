from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from filters.chat_types import ChatTypeFilter, IsConfirmedUser, IsAdmin

user_private_admin_router = Router()
user_private_admin_router.message.filter(ChatTypeFilter(['private']),IsAdmin())
user_private_admin_router.callback_query.filter(IsAdmin())


@user_private_admin_router.message(CommandStart())
async def start_cmd(message: types.Message,
                    session: AsyncSession,
                    state: FSMContext):
    await state.clear()
    await message.answer('Добро пожаловть Администратор.')