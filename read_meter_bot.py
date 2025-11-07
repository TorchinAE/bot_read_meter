import asyncio
import logging
import os
from logging.handlers import RotatingFileHandler

from aiogram import Bot, Dispatcher, types
from dotenv import load_dotenv

import dbase.storage
from dbase.orm_query import orm_get_words, orm_get_admin_list

load_dotenv()

from common.bot_cmds_list import private
from dbase.orm_db import create_db, session_maker
from handlers.admin_private import user_private_admin_router
from handlers.user_group import user_group_router, cleanup_expired_bans, \
    get_admin
from handlers.user_private import user_private_router
from handlers.user_private_comfirmed import user_private_confirmed_router
from middlewares.db import DataBaseSession


log_formatter = logging.Formatter(
    "%(asctime)s, %(levelname)s, %(message)s /%(funcName)s/"
)
log_handler = RotatingFileHandler(
    "log_read_meter_telebot.log",
    maxBytes=50_000_000,
    backupCount=5,
    encoding="utf-8"
)
log_handler.setFormatter(log_formatter)

logging.getLogger().setLevel(logging.ERROR)
logging.getLogger().addHandler(log_handler)

bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
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
        commands=private, scope=types.BotCommandScopeAllPrivateChats()
    )
    async with session_maker() as session:
        words = set(await orm_get_words(session))
        dbase.storage.restricted_words = set(word.lower() for word in words)

    asyncio.create_task(cleanup_expired_bans(session_maker, bot, interval=60))
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(create_db())
    asyncio.run(main())
