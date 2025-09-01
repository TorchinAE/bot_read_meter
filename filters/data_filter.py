from aiogram import types
from aiogram.fsm.context import FSMContext


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