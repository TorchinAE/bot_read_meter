from string import punctuation

from aiogram import types, Router, Bot
from aiogram.filters import Command

from filters.chat_types import ChatTypeFilter

user_group_router = Router()
user_group_router.message.filter(ChatTypeFilter(['group', 'supergroup']))

restricted_words = {'придурок', 'чудо'}


def clean_text(text: str):
    return text.translate(str.maketrans('', '', punctuation))


@user_group_router.message(Command('admin'))
async def get_admin(message: types.Message, bot: Bot):
    chat_id = message.chat.id
    admin_list = await  bot.get_chat_administrators(chat_id)
    admin_list = [
        member.user.id
        for member in admin_list
        if member.status =='creator' or member.status == 'administrator'
    ]
    bot.my_admin_list = admin_list
    if message.from_user.id in admin_list:
        await  message.delete()


@user_group_router.edited_message()
@user_group_router.message()
async def cleaner(message: types.Message):
    if restricted_words.intersection(clean_text(message.text.lower()).split()):
        await message.answer(
            f'{message.from_user.first_name}, соблюдайте порядок в чате!'
            )
        await message.delete()
