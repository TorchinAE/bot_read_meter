from calendar import SATURDAY

from aiogram.fsm.state import State, StatesGroup


class AddUser(StatesGroup):
    name = State()
    apartment = State()
    phone = State()


class AddMeter(StatesGroup):
    water_hot_kitchen = State()
    water_hot_bath = State()
    water_cold_kitchen = State()
    water_cold_bath = State()


class ChangeMeter(StatesGroup):
    apartment = State()
    water_hot_kitchen = State()
    water_hot_bath = State()
    water_cold_kitchen = State()
    water_cold_bath = State()


class PorchMessage(StatesGroup):
    porch = State()
    text = State()
    confirm = State()
    apart = State()


class SetApart(StatesGroup):
    apartment = State()


class SetApartMetr(StatesGroup):
    apartment = State()


class ChangeWords(StatesGroup):
    input_word = State()
    edit_word = State()
    delete_word = State()
    add_word = State()


class GetPower(StatesGroup):
    apartment = State()
    t0 = State()
    t1 = State()
    t2 = State()
    next_ap = State ()