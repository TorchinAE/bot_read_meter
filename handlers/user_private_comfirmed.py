from aiogram import F, types, Router
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from dbase.orm_query import (orm_get_user, orm_get_meter_from_user_month_year,
                             orm_add_update_meter, orm_get_user_meters_last)
from filters.chat_types import ChatTypeFilter, IsConfirmedUser
from filters.data_filter import validate_data_meter
from handlers.states import AddMeter
from kbds.kbds import get_user_main_btns, btns

user_private_confirmed_router = Router()
user_private_confirmed_router.message.filter(ChatTypeFilter(['private']),
                                             IsConfirmedUser()
                                             )
user_private_confirmed_router.callback_query.filter(IsConfirmedUser())


@user_private_confirmed_router.message(CommandStart())
async def start_cmd(message: types.Message,
                    session: AsyncSession,
                    state: FSMContext):
    await state.clear()
    user = await orm_get_user(session, message.from_user.id)
    text_mgs = f'Приветствую Вас, {user.name}! Выберите счётчик.'
    await message.answer(text_mgs, reply_markup=get_user_main_btns(btns))


@user_private_confirmed_router.message(Command('menu'))
async def menu_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer('Выберите счётчик.',
                         reply_markup=get_user_main_btns(btns))


@user_private_confirmed_router.callback_query(F.data == "all")
async def all_cmd(callback_query: types.CallbackQuery,
                  session: AsyncSession,
                  state: FSMContext):
    await state.clear()
    meter = await orm_get_user_meters_last(session, callback_query.from_user.id)
    data = meter.updated.strftime("%d-%m-%y")

    await callback_query.message.answer(
        f'Показания на {data}'
        f'\n\nГорячая вода кухня - {meter.water_hot_kitchen}'
        f'\nГорячая вода СУ - {meter.water_hot_bath}'
        f'\nХолодная вода кухня - {meter.water_cold_kitchen}'
        f'\nХолодная вода СУ - {meter.water_cold_bath}')
    await callback_query.answer()


@user_private_confirmed_router.callback_query(F.data)
async def set_meter_cmd(callback_query: types.CallbackQuery,
                        session: AsyncSession,
                        state: FSMContext):

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

    if action == "water_hot_kitchen":
        current_value = meter.water_hot_kitchen if meter else None
    elif action == "water_cold_kitchen":
        current_value = meter.water_cold_kitchen if meter else None
    elif action == "water_hot_bath":
        current_value = meter.water_hot_bath if meter else None
    elif action == "water_cold_bath":
        current_value = meter.water_cold_bath if meter else None

    msg = (f'Текущие показания {current_value}.'
           '\nВведите показания счётчика.')
    await callback_query.message.answer(msg)
    await state.set_state(state_mapping[action])
    current_state = await state.get_state()
    await callback_query.answer()


@user_private_confirmed_router.message(F.text, StateFilter('*'))
async def save_meter_cmd(message: types.Message,
                         session: AsyncSession,
                         state: FSMContext
):
    water_hot_kitchen_data = None
    water_cold_kitchen_data = None
    water_hot_bath_data = None
    water_cold_bath_data = None
    meter = await orm_get_meter_from_user_month_year(session,
                                                     message.from_user.id)
    current_state = await state.get_state()
    print('current_state==', current_state)
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
    validate = await validate_data_meter(message, message.text, meter_value)
    print('validate==',validate, 'meter_value==', meter_value)
    if not validate or current_state is None:
        return
    await orm_add_update_meter(session,
                               message.from_user.id,
                               water_hot_kitchen=water_hot_kitchen_data,
                               water_cold_kitchen=water_cold_kitchen_data,
                               water_hot_bath=water_hot_bath_data,
                               water_cold_bath=water_cold_bath_data,
                               )
    await state.clear()
    await message.answer('✅ Сохранено')
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
    print(f"Получен user_private_confirmed_router callback_data: '{callback_query.data}'")
    await callback_query.answer("Обработка не найдена для: " + callback_query.data)
