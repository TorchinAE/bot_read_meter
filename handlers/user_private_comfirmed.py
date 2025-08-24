from aiogram import F, types, Router
from aiogram.filters import CommandStart, Command
from filters.chat_types import ChatTypeFilter, IsConfirmedUser

user_private_confirmed_router = Router()
user_private_confirmed_router.message.filter(ChatTypeFilter(['private']), IsConfirmedUser())
user_private_confirmed_router.callback_query.filter(IsConfirmedUser())

@user_private_confirmed_router.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.answer('На старт! Это бот для передачи показаний счётчиков.')


@user_private_confirmed_router.message(Command('menu'))
async def menu_command(message: types.Message):
    await message.answer('Вот твоё меню:')


@user_private_confirmed_router.callback_query(F.data == "cancel_data")
async def cancel_cmd(callback_query: types.CallbackQuery):
    await callback_query.answer('Вы отменили операцию.')
    await callback_query.message.answer('Был рад пообщаться user_private_confirmed_router.')


@user_private_confirmed_router.callback_query()
async def debug_all_callbacks(callback_query: types.CallbackQuery):
    print(f"Получен user_private_confirmed_router callback_data: '{callback_query.data}'")
    await callback_query.answer("Обработка не найдена для: " + callback_query.data)
