from calendar import SATURDAY

from aiogram.fsm.state import StatesGroup, State


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