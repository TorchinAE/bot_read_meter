import asyncio

from dotenv import load_dotenv
import os
from aiogram import Bot, Dispatcher, types

import dbase.storage
from dbase.orm_query import orm_get_words


load_dotenv()

from middlewares.db import DataBaseSession

from dbase.orm_db import create_db, session_maker
from handlers.admin_private import user_private_admin_router
from handlers.user_private_comfirmed import user_private_confirmed_router
from handlers.user_private import user_private_router
from handlers.user_group import user_group_router
from common.bot_cmds_list import private


bot = Bot(token=os.getenv('TELEGRAM_TOKEN'))
bot.my_admin_list = []
dp = Dispatcher()

dp.include_router(user_private_admin_router)
dp.include_router(user_private_confirmed_router)
dp.include_router(user_private_router)
dp.include_router(user_group_router)


async def main():
    dp.update.middleware(DataBaseSession(session_pool=session_maker))
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(
        commands=private,
        scope=types.BotCommandScopeAllPrivateChats()
    )
    async with session_maker() as session:
        words = set(await orm_get_words(session))
        dbase.storage.restricted_words = set(word.lower() for word in words)

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(create_db())
    asyncio.run(main())
