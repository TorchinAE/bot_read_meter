from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_user_main_btns(btns: dict[str, str], sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()
    for text, call_back in btns.items():
        keyboard.add(InlineKeyboardButton(text=text, callback_data=call_back))
        print(f'*{text}*, *{call_back}*')
    return keyboard.adjust(*sizes).as_markup()

btns = {"Горячая вода кухня": "water_hot_kitchen",
        "Горячая вода СУ": "water_hot_bath",
        "Холодная вода кухня": "water_cold_kitchen",
        "Холодная вода СУ": "water_cold_bath",
        "Текущие показания": "all",
        }