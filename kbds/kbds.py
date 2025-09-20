from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_user_main_btns(btns: dict[str, str], sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()
    for text, call_back in btns.items():
        keyboard.add(InlineKeyboardButton(text=text, callback_data=call_back))
    return keyboard.adjust(*sizes).as_markup()

btns = {"Горячая вода кухня": "water_hot_kitchen",
        "Горячая вода СУ": "water_hot_bath",
        "Холодная вода кухня": "water_cold_kitchen",
        "Холодная вода СУ": "water_cold_bath",
        "Текущие показания": "all",
        }

btns_cnl = {"Горячая вода кухня": "water_hot_kitchen",
        "Горячая вода СУ": "water_hot_bath",
        "Холодная вода кухня": "water_cold_kitchen",
        "Холодная вода СУ": "water_cold_bath",
        "Выйти": "cancel",
        }

btns_admin = {"Подтвердить жильца": "confirm_user",
              "Коррекция данных счётчика": "edit_meter",
              "Личное сообщение подъезду": "msg_porch",
              "Запросить показания": "get_meter_all",
              "Данные по квартире": "get_data_apart",
              }

btns_del_confirm = {'Подтвердить': 'conf_user',
                    'Удалить': 'del_user'
                    }

btns_yes_no = {'Отправить': 'yes',
               'Отмена': 'cancel'}