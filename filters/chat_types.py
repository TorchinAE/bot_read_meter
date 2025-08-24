from aiogram.filters import Filter
from aiogram import types, Bot
from sqlalchemy.ext.asyncio import AsyncSession

from dbase.orm_query import orm_get_confirmed


class ChatTypeFilter(Filter):
    def __init__(self, chat_types: list[str]) -> None:
        self.chat_types = chat_types

    async def __call__(self, message: types.Message) -> bool:
        return message.chat.type in self.chat_types


class IsAdmin(Filter):
    def __init__(self) -> None:
        pass

    async def __call__(self, message: types.Message, bot: Bot) -> bool:
        if message.from_user.id in bot.my_admins_list:
            print('IsAdmin')
        else:
            print('NO Admin')
        return message.from_user.id in bot.my_admins_list


class IsConfirmedUser(Filter):
    def __init__(self) -> None:
        pass

    async def __call__(self, message: types.Message, bot: Bot, session: AsyncSession) -> bool:
        user_id = message.from_user.id
        print('IsConfirmedUser== ', await orm_get_confirmed(session, user_id))
        return await orm_get_confirmed(session, user_id)