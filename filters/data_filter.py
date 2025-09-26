from aiogram import types
from aiogram.fsm.context import FSMContext

from handlers.const import APARTMENTCOUNT


async def validate_data_meter(message: types.Message,
                              state: FSMContext,
                              data_meter:str,
                              now_meter:int = 0
                              ) -> bool:
    current_state = await state.get_state()
    if current_state is None:
        return False
    if not data_meter.isdigit():
        await message.answer('Не верный ввод.\nОжидается положительное число.')
        return False
    if now_meter is None:
        return True
    if int(data_meter) < now_meter:
        await message.answer('Не верный ввод.\nПоказания не могут быть меньше текущих.'
                             f'\nТекущие показания: {now_meter}'
                             '\nПовторите ввод')
        return False
    return True

async def validate_porch(message: types.Message) ->bool:
    num_porch = message.text
    if not num_porch.isdigit() or int(num_porch) > 5:
        await message.answer('Не верный ввод.\nОжидается число 1 - 5')
        return False
    return True


async def validate_apart(message: types.Message) ->bool:
    apart = message.text
    if not apart.isdigit():
        await message.answer('Ожидается число')
        return False
    if int(apart) > APARTMENTCOUNT:
        await message.answer(
            f'Номер квартиры не может быть больше {APARTMENTCOUNT}'
        )
        return False
    print('validate_apart==True')
    return True
