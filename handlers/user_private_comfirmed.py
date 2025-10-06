from datetime import datetime

from aiogram import F, Router, types
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from dbase.orm_query import (
    orm_add_update_meter,
    orm_get_meter_from_user_month_year,
    orm_get_user_meters_last,
    orm_get_user_tele,
)
from filters.chat_types import ChatTypeFilter, IsConfirmedUser
from filters.data_filter import validate_data_meter
from handlers.states import AddMeter
from kbds.kbds import btns, get_user_main_btns

user_private_confirmed_router = Router()
user_private_confirmed_router.message.filter(
    ChatTypeFilter(["private"]), IsConfirmedUser()
)
user_private_confirmed_router.callback_query.filter(IsConfirmedUser())


@user_private_confirmed_router.message(CommandStart())
async def start_cmd(message: types.Message, session: AsyncSession, state: FSMContext):
    await state.clear()
    user = await orm_get_user_tele(session, message.from_user.id)
    text_mgs = f"Приветствую Вас, {user.name}! Выберите счётчик."
    await message.answer(text_mgs, reply_markup=get_user_main_btns(btns))


@user_private_confirmed_router.message(Command("menu"))
async def menu_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Чтобы передать показания выберите счётчик.",
        reply_markup=get_user_main_btns(btns),
    )


@user_private_confirmed_router.message(Command("about"))
async def about_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Коротко о нас... Рождественский дом 6" "\nВыберите команду из Menu"
    )


@user_private_confirmed_router.callback_query(F.data == "all")
async def all_cmd(
    callback_query: types.CallbackQuery, session: AsyncSession, state: FSMContext
):
    await state.clear()
    meter = await orm_get_user_meters_last(session, callback_query.from_user.id)
    data_now = datetime.now()
    if meter:
        last_update_date = meter.updated
        msg = (
            f'Показания на {last_update_date.strftime("%d.%m.%Y")}'
            "\n\nГорячая вода кухня - "
            f'{meter.water_hot_kitchen if meter.water_hot_kitchen else "Не найдено"}'
            "\nГорячая вода СУ - "
            f'{meter.water_hot_bath if meter.water_hot_bath else "Не найдено"}'
            "\nХолодная вода кухня - "
            f'{meter.water_cold_kitchen if meter.water_cold_kitchen else "Не найдено"}'
            "\nХолодная вода СУ - "
            f'{meter.water_cold_bath if meter.water_cold_bath else "Не найдено"}'
        )

        if (
            data_now.month != last_update_date.month
            or data_now.year != last_update_date.year
        ):
            msg += (
                "\n\nПоказания на текущий месяц не обнаружены. " "Передайте показания"
            )
    else:
        msg = f'Показания на {data_now.strftime("%d-%m-%y")} не найдены.'

    await callback_query.message.answer(msg)
    await callback_query.answer()
    await menu_cmd(callback_query.message, state)


@user_private_confirmed_router.callback_query(F.data)
async def set_meter_cmd(
    callback_query: types.CallbackQuery, session: AsyncSession, state: FSMContext
):

    action = callback_query.data

    # Словарь: сопоставление callback_data и состояний
    state_mapping = {
        "water_hot_kitchen": AddMeter.water_hot_kitchen,
        "water_cold_kitchen": AddMeter.water_cold_kitchen,
        "water_hot_bath": AddMeter.water_hot_bath,
        "water_cold_bath": AddMeter.water_cold_bath,
    }

    meter = await orm_get_user_meters_last(session, callback_query.from_user.id)
    current_value = None
    name_meter = ""
    if action == "water_hot_kitchen":
        current_value = meter.water_hot_kitchen if meter else None
        name_meter = "Горячая вода кухня"
    elif action == "water_cold_kitchen":
        current_value = meter.water_cold_kitchen if meter else None
        name_meter = "Холодная вода кухня"
    elif action == "water_hot_bath":
        current_value = meter.water_hot_bath if meter else None
        name_meter = "Горячая вода СУ"
    elif action == "water_cold_bath":
        current_value = meter.water_cold_bath if meter else None
        name_meter = "Холодная вода СУ"

    msg = (
        f"{name_meter}\nТекущие показания - "
        f'{current_value if current_value else " не найдены."}'
        "\nВведите показания счётчика."
    )
    await callback_query.message.answer(msg)
    await state.set_state(state_mapping[action])
    await callback_query.answer()


@user_private_confirmed_router.message(F.text, StateFilter("*"))
async def save_meter_cmd(
    message: types.Message, session: AsyncSession, state: FSMContext
):
    water_hot_kitchen_data = None
    water_cold_kitchen_data = None
    water_hot_bath_data = None
    water_cold_bath_data = None
    meter = await orm_get_meter_from_user_month_year(session, message.from_user.id)
    current_state = await state.get_state()
    print("current_state==", current_state)
    meter_value = None
    if current_state == AddMeter.water_hot_kitchen:
        meter_value = meter.water_hot_kitchen if meter else None
        water_hot_kitchen_data = message.text
    elif current_state == AddMeter.water_cold_kitchen:
        meter_value = meter.water_cold_kitchen if meter else None
        water_cold_kitchen_data = message.text
    elif current_state == AddMeter.water_hot_bath:
        meter_value = meter.water_hot_bath if meter else None
        water_hot_bath_data = message.text
    elif current_state == AddMeter.water_cold_bath:
        meter_value = meter.water_cold_bath if meter else None
        water_cold_bath_data = message.text
    validate = await validate_data_meter(message, state, message.text, meter_value)
    print("validate==", validate, "meter_value==", meter_value)
    if not validate or current_state is None:
        return
    await orm_add_update_meter(
        session,
        message.from_user.id,
        water_hot_kitchen=water_hot_kitchen_data,
        water_cold_kitchen=water_cold_kitchen_data,
        water_hot_bath=water_hot_bath_data,
        water_cold_bath=water_cold_bath_data,
    )
    await state.clear()
    await message.answer("✅ Сохранено")
    await menu_cmd(message, state)


@user_private_confirmed_router.message(Command("cancel"))
@user_private_confirmed_router.message(F.text.casefold() == "cancel")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.set_state(state=None)
    await message.answer("Отменено", reply_markup=ReplyKeyboardRemove())


@user_private_confirmed_router.callback_query()
async def debug_all_callbacks(callback_query: types.CallbackQuery):
    print(
        f"Получен user_private_confirmed_router callback_data: '{callback_query.data}'"
    )
    await callback_query.answer("Обработка не найдена для: " + callback_query.data)
