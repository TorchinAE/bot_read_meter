from string import punctuation

from aiogram import types, Router, Bot, F
from aiogram.filters import Command

import dbase.storage
from filters.chat_types import ChatTypeFilter
from kbds.kbds import get_user_main_btns

user_group_router = Router()
user_group_router.message.filter(ChatTypeFilter(['group', 'supergroup']))

def clean_text(text: str):
    return text.translate(str.maketrans('', '', punctuation))


@user_group_router.message(Command('admin'))
async def get_admin(message: types.Message, bot: Bot):
    chat_id = message.chat.id
    admin_list = await  bot.get_chat_administrators(chat_id)
    admin_list = [
        member.user.id
        for member in admin_list
        if member.status == 'creator' or member.status == 'administrator'
    ]
    bot.my_admin_list = admin_list
    if message.from_user.id in admin_list:
        await  message.delete()


@user_group_router.edited_message()
@user_group_router.message()
async def cleaner(message: types.Message, bot:Bot):
    if not message.text:
        return

    if dbase.storage.restricted_words.intersection(clean_text(message.text.lower()).split()):
        admins = await bot.get_chat_administrators(message.chat.id)
        creator_id = None
        for admin in admins:
            if admin.status == "creator":
                creator_id = admin.user.id
                break

        await message.answer(
            f'{message.from_user.first_name}, соблюдайте порядок в чате!'
            )

        if creator_id:
            text = (f'⚠️ Пользователь {message.from_user.first_name} '
                    f'(ID: {message.from_user.id})\n'
                    f'в чате {message.chat.title} матерится:\n'
                    f'"{message.text}"')
            btns_block = {'Заблокировать': f'block_user_{message.from_user.id}_{message.chat.id}',
                          'Игнорировать': 'cancel'}
            await message.bot.send_message(
                chat_id=creator_id,
                text=text,
                reply_markup=get_user_main_btns(btns_block))
        await message.delete()


