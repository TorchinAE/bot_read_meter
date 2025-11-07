import asyncio
from datetime import datetime, timezone
from string import punctuation

from aiogram import Bot, Router, types
from aiogram.filters import Command
from aiogram.types import ChatMemberUpdated
from sqlalchemy.ext.asyncio import AsyncSession

import dbase.storage
from dbase.orm_query import post_block_user, orm_add_admins, get_block_users, \
    remove_block_user
from filters.chat_types import ChatTypeFilter
from handlers.admin_private import logger
from kbds.kbds import get_user_main_btns

user_group_router = Router()
user_group_router.message.filter(ChatTypeFilter(["group", "supergroup"]))

async def cleanup_expired_bans(session_maker, bot: Bot, interval: int = 60):
    while True:
        try:
            async with session_maker() as session:
                ban_users = await get_block_users(session)
                now = datetime.now(timezone.utc)
                for ban in ban_users:
                    unblock = getattr(ban, "unblock_time", None)
                    if unblock:
                        if unblock.tzinfo is None:
                            unblock = unblock.replace(tzinfo=timezone.utc)
                        if unblock <= now:
                            await remove_block_user(session, ban.user_tele_id)
                            try:
                                await bot.send_message(
                                    chat_id=ban.user_tele_id,
                                    text="Срок вашей блокировки в чате истёк — вы разблокированы."
                                )
                            except Exception:
                                pass
        except Exception as e:
            logger.error(f"cleanup_expired_bans error: {e}")
        await asyncio.sleep(interval)


def clean_text(text: str):
    return text.translate(str.maketrans("", "", punctuation))


@user_group_router.message(Command("admin"))
async def get_admin(message: types.Message, bot: Bot, session: AsyncSession):
    chat_id = message.chat.id
    try:
        chat_admins = await bot.get_chat_administrators(chat_id)
        admin_tele_ids = [
            admin.user.id
            for admin in chat_admins
            if admin.status in ("creator", "administrator") and not admin.user.is_bot
        ]
        await orm_add_admins(session, admin_tele_ids, chat_id, bot)
        bot.my_admin_list = admin_tele_ids

        if message.from_user.id in admin_tele_ids:
            await message.delete()

    except Exception as e:
        logger.error(f"Ошибка при обработке /admin: {e}")
        await message.answer("Не удалось обновить список админов.")

# TODO обновить место получения админов


async def delete_if_blocked(message: types.Message, session: AsyncSession) -> bool:
    """
    Проверяет, заблокирован ли автор сообщения.
    Если заблокирован — удаляет сообщение и возвращает True.
    """
    try:
        ban_users = await get_block_users(session)
        banned_tele_ids = {ban.user_tele_id for ban in ban_users}
    except Exception as e:
        logger.error(f"Ошибка получения списка заблокированных: {e}")
        return False

    if not message.from_user:
        return False

    if message.from_user.id in banned_tele_ids:
        try:
            await message.delete()
            await message.bot.send_message(
                chat_id=message.from_user.id,
                text='Вы заблокированы и не можете отправлять сообщения в этот чат.'            )
            logger.info(
                f"Удалено сообщение заблокированного пользователя {message.from_user.id} в чате {message.chat.id}"
            )
        except Exception as e:
            logger.error(f"Не удалось удалить сообщение заблокированного пользователя: {e}")
        return True

    return False


@user_group_router.edited_message()
@user_group_router.message()
async def cleaner(message: types.Message,
                  bot: Bot,
                  session: AsyncSession):
    if not message.text:
        return

    if await delete_if_blocked(message, session):
        return

    if dbase.storage.restricted_words.intersection(
        clean_text(message.text.lower()).split()
    ):
        admins = await bot.get_chat_administrators(message.chat.id)
        creator_id, creator_name = None, None
        for admin in admins:
            if admin.status == "creator":
                creator_id = admin.user.id
                creator_name = admin.user.username
                break

        await message.answer(
            f"{message.from_user.first_name}, соблюдайте порядок в чате!"
        )
        await message.delete()
        ban_write_id = await post_block_user(
            session=session,
            user_tele_id=message.from_user.id,
            ban_admin_tele_id=creator_id,
            chat_id=message.chat.id,
            name_admin=creator_name,
            reason=message.text,
            unblock_time=None
        )
        if creator_id:
            text = (
                f"⚠️ Пользователь {message.from_user.first_name} "
                f"(ID: {message.from_user.id})\n"
                f"в чате {message.chat.title} матерится:\n"
                f'"{message.text}"'
            )
            btns_block = {
                "Заблокировать": f"block_{ban_write_id}",
                "Игнорировать": "cancel",
            }
            await message.bot.send_message(
                chat_id=creator_id,
                text=text,
                reply_markup=get_user_main_btns(btns_block),
            )


@user_group_router.chat_member()
async def on_user_added(event: ChatMemberUpdated, bot:Bot, session: AsyncSession):
    user = event.new_chat_member.user
    ban_users = await get_block_users(session)
    banned_tele_ids = {ban.user_tele_id for ban in ban_users}
    logger.info(
        f"Проверка входящего  {user.full_name} (ID: {user.id}) в {ban_users}")
    if (not user.is_bot) or (user.id in banned_tele_ids):

        if event.new_chat_member.status not in {"left", "kicked", "restricted"}:
            text = f'Добро пожаловать, {user.full_name}'
            await event.bot.send_message(event.chat.id, text)

    else:
        chat_id = event.chat.id
        await kick_user(bot, chat_id, user.id)


async def kick_user(bot:Bot, chat_id, user_id):
    await bot.ban_chat_member(
        chat_id=chat_id,
        user_id=user_id,
        until_date=1
    )

    logger.info(
        f"Кикнут  ID: {user_id} из чата {chat_id}")