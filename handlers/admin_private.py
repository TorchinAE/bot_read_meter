from aiogram import Router, types, F, Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from aiogram.filters import CommandStart, StateFilter, Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from dbase.orm_query import orm_get_unconfirmed_user_last, \
    orm_del_user, orm_get_user_tele, orm_get_users_to_apart, \
    orm_get_users_confirm, orm_get_user_apartment, orm_get_user_meters_last, \
    orm_add_update_meter
from filters.chat_types import ChatTypeFilter, IsAdmin
from filters.data_filter import validate_porch, validate_apart, \
    validate_data_meter
from handlers.const import PORCH_APART
from handlers.states import PorchMessage, SetApart, ChangeMeter
from kbds.kbds import btns_admin, get_user_main_btns, btns_yes_no, btns, \
    btns_cnl

user_private_admin_router = Router()
user_private_admin_router.message.filter(ChatTypeFilter(['private']),IsAdmin())
user_private_admin_router.callback_query.filter(IsAdmin())

@user_private_admin_router.message(Command('menu'))
async def nemu_cmd(message: types.Message, state: FSMContext):
    await start_cmd(message, state)


@user_private_admin_router.message(Command('about'))
async def about_cmd(message: types.Message, state: FSMContext):
    text_mgs = (f'Приветствую Вас, {message.from_user.username}!\n'
                 'Это бот для жителей дома №6 мкр. Рождественский.'
                 '\nВы являетесь администратором.'
                 '\nДля начала работы отправьте команду /start')
    await message.answer(text_mgs)
    await start_cmd(message, state)


@user_private_admin_router.message(CommandStart())
async def start_cmd(message: types.Message,
                    state: FSMContext):
    await state.clear()
    text_mgs = 'Добро пожаловать , Администратор'
    await message.answer(text_mgs, reply_markup=get_user_main_btns(btns_admin))


@user_private_admin_router.callback_query(F.data == "cancel")
async def cancel_cmd(callback: types.CallbackQuery,
                     state: FSMContext):
    await callback.answer()
    await start_cmd(callback.message, state)


@user_private_admin_router.callback_query(F.data == "confirm_user")
async def confirm_user_cmd(callback: types.CallbackQuery,
                           session: AsyncSession):
    user = await orm_get_unconfirmed_user_last(session)
    if not user:
        await callback.answer("Нет неподтверждённых пользователей.", show_alert=True)
        return
    user_info = (
        f"👤 <b>Имя:</b> {user.name}\n"
        f"👤 <b>Квартира:</b> {user.apartment}\n"
        f"📞 <b>Телефон:</b> {user.phone}\n"
        f"🆔 <b>Telegram ID:</b> {user.tele_id}\n"
        f"📅 <b>Дата регистрации:</b> {user.created.strftime('%d.%m.%Y %H:%M') if user.created else '—'}"
    )
    await callback.message.edit_text(
        user_info,
        reply_markup=get_user_main_btns(
            {'Подтвердить': f'conf_user_{user.tele_id}',
             'Удалить': f'del_user_{user.tele_id}'}
        ),
        parse_mode="HTML"
    )
    await callback.answer()


@user_private_admin_router.callback_query(F.data.startswith("conf_user"))
async def conf_user_cmd(callback: types.CallbackQuery,
                      session: AsyncSession,
                      bot: Bot,
                      state: FSMContext):
    tele_id = int(callback.data.split('_')[-1])
    user = await orm_get_user_tele(session, tele_id)
    user.confirmed = True
    await session.commit()
    await bot.send_message(
        chat_id=user.tele_id,
        text=f"✅ Вас подтвердили! Добро пожаловать, {user.name}."
    )
    await callback.answer(
        f'Пользователь {user.name} - кв {user.apartment} подтвержден.',
        show_alert=True)
    await start_cmd(callback.message, state)


@user_private_admin_router.callback_query(F.data.startswith("del_user"))
async def del_user_cmd(callback: types.CallbackQuery,
                      session: AsyncSession,
                      bot: Bot):
    tele_id = int(callback.data.split('_')[-1])
    user = await orm_get_user_tele(session, tele_id)
    await orm_del_user(session, user.tele_id)
    await callback.answer(
        f'Пользователь {user.name} - кв {user.apartment} удалён.',
        show_alert=True)
    await bot.send_message(
        chat_id=user.tele_id,
        text=(f"❌ Вы не прошли проверку, {user.name}. Похоже Вы не из наших."
              '\nПрощайте.')
    )

@user_private_admin_router.callback_query(F.data == "edit_meter")
async def edit_meter_cmd(callback: types.CallbackQuery,
                         bot: Bot,
                         state: FSMContext):
    user_tele_id = callback.from_user.id
    await bot.send_message(user_tele_id, text='Введите номер квартиры')
    await state.set_state(ChangeMeter.apartment)
    await callback.answer()

@user_private_admin_router.callback_query(F.data.startswith('msg_porch'))
async def msg_porch_cmd(callback: types.CallbackQuery,
                        bot: Bot,
                        state: FSMContext):
    user_tele_id = callback.from_user.id
    await bot.send_message(user_tele_id, text='Введите номер подъезда')
    await state.set_state(PorchMessage.porch)
    await callback.answer()


@user_private_admin_router.message(ChangeMeter.apartment, F.text)
async def input_apart(message: types.Message,
                      session: AsyncSession,
                      state: FSMContext):
    if await validate_apart(message):
        user = await orm_get_user_apartment(session, message.text)
        if user is None:
            await message.answer('Квартира не найдена')
            await start_cmd(message,state)
            return

        await state.update_data(apartment=message.text)
        meter = await  orm_get_user_meters_last(session, user.tele_id)
        user_info = f'Текущие показания кв {user.apartment}:\n'
        if meter:
            user_info += (
                f"🚰 <b>Счётчики горячей воды:</b> кухня - {meter.water_hot_kitchen if meter.water_hot_kitchen else 'Не найдено'}    СУ - {meter.water_hot_bath if meter.water_hot_bath else 'Не найдено'}\n"
                f"🚰 <b>Счётчики холодной воды:</b> кухня - {meter.water_cold_kitchen if meter.water_cold_kitchen else 'Не найдено'}    СУ - {meter.water_cold_bath if meter.water_cold_bath else 'Не найдено'}\n"
            )
        else:
            user_info = 'Показания не обнаружены'
        await message.answer(user_info, parse_mode="HTML", reply_markup=get_user_main_btns(btns))


@user_private_admin_router.message(PorchMessage.porch, F.text)
async def input_porch(message: types.Message,
                      state: FSMContext):
    if await validate_porch(message):
        await state.update_data(porch=message.text)
        await message.answer('Введите сообщение')
        await state.set_state(PorchMessage.text)


@user_private_admin_router.message(PorchMessage.text, F.text)
async def input_text(message: types.Message,
                      state: FSMContext):
    await state.update_data(text=message.text)
    data = await state.get_data()
    await message.answer(f'В {data.get("porch")} подъезд будет отправлено'
                         f' сообщение:\n{data.get("text")}',
                         reply_markup=get_user_main_btns(btns_yes_no)
                         )
    await state.set_state(PorchMessage.confirm)

@user_private_admin_router.callback_query(PorchMessage.confirm)
async def send_msg_porch(callback: types.CallbackQuery,
                         session: AsyncSession,
                         bot: Bot,
                         state: FSMContext):
    if callback.data == 'yes':
        data = await state.get_data()
        porch = int(data.get('porch'))
        aparts = PORCH_APART[porch]
        users = await orm_get_users_to_apart(session, aparts[0], aparts[1])
        for user in users:
            try:
                await bot.send_message(user.tele_id, text=data.get('text'))
            except TelegramForbiddenError:
                await orm_del_user(session, user.tele_id)
                txt = (f'Пользователь {user.tele_id} - {user.apartment} '
                       'заблокировал бота и был удалён.')
                await bot.send_message(callback.from_user.id, text=txt)
            except TelegramBadRequest as e:
                print(f"Неверный запрос при отправке {user.tele_id}: {e}")
            except Exception as e:
                print(f"Неизвестная ошибка при отправке {user.tele_id}: {e}")
        await callback.answer('Сообщения разосланы', show_alert=True)
    elif callback.data == 'cancel':
        await state.clear()
        await callback.answer('Отправка отменена', show_alert=True)
    await start_cmd(callback.message, state)


@user_private_admin_router.callback_query(F.data.startswith('get_meter_all'))
async def get_meter_all_cmd(callback: types.CallbackQuery,
                            session: AsyncSession,
                            bot: Bot):
    users = await orm_get_users_confirm(session)
    for user in users:
        try:
            await bot.send_message(user.tele_id,
                                   'Здравствуйте.\nПрошу Вас передать '
                                    'показания приборов учёта.',
                                   reply_markup=get_user_main_btns(btns))
        except TelegramForbiddenError:
            print(
                f"Пользователь {user.tele_id} - {user.apartment} заблокировал бота")
            await orm_del_user(session, user.tele_id)
            txt = (f'Пользователь {user.tele_id} - {user.apartment} '
                   'заблокировал бота и был удалён.')
            await bot.send_message(callback.from_user.id, text=txt)
        except TelegramBadRequest as e:
            print(f"Неверный запрос при отправке {user.tele_id}: {e}")
        except Exception as e:
            print(f"Неизвестная ошибка при отправке {user.tele_id}: {e}")
    await callback.answer()


@user_private_admin_router.callback_query(F.data == 'get_data_apart')
async def get_data_apart_cmd(callback: types.CallbackQuery,
                        bot: Bot,
                        state: FSMContext):
    await bot.send_message(callback.from_user.id,
                           'Введите номер квартиры')
    await callback.answer()
    await state.set_state(SetApart.apartment)

async def show_meter_info(
    message: types.Message,
    session: AsyncSession,
    state: FSMContext,
    apartment: str
):
    user = await orm_get_user_apartment(session, apartment)
    if user is None:
        await message.answer('Квартира не найдена')
        await start_cmd(message, state)
        return

    await state.update_data(apartment=apartment)  # Обновляем состояние

    meter = await orm_get_user_meters_last(session, user.tele_id)

    user_info = f'Текущие показания кв {user.apartment}:\n'
    if meter:
        user_info += (
            f"🚰 <b>Счётчики горячей воды:</b> кухня - {meter.water_hot_kitchen if meter.water_hot_kitchen else 'Не найдено'}    СУ - {meter.water_hot_bath if meter.water_hot_bath else 'Не найдено'}\n"
            f"🚰 <b>Счётчики холодной воды:</b> кухня - {meter.water_cold_kitchen if meter.water_cold_kitchen else 'Не найдено'}    СУ - {meter.water_cold_bath if meter.water_cold_bath else 'Не найдено'}\n"
        )
    else:
        user_info = 'Показания не обнаружены'

    await message.answer(user_info, parse_mode="HTML", reply_markup=get_user_main_btns(btns_cnl))


@user_private_admin_router.message(SetApart.apartment, F.text)
async def send_info_apart(message: types.Message,
                          session: AsyncSession,
                          state: FSMContext):
    if not await validate_apart(message):
        return

    await show_meter_info(message, session, state, message.text)


@user_private_admin_router.callback_query(F.data)
async def set_meter_cmd(callback_query: types.CallbackQuery,
                        session: AsyncSession,
                        state: FSMContext):

    action = callback_query.data

    # Словарь: сопоставление callback_data и состояний
    state_mapping = {
        "water_hot_kitchen": ChangeMeter.water_hot_kitchen,
        "water_cold_kitchen": ChangeMeter.water_cold_kitchen,
        "water_hot_bath": ChangeMeter.water_hot_bath,
        "water_cold_bath": ChangeMeter.water_cold_bath,
    }
    data = await state.get_data()
    user = await orm_get_user_apartment(session, data['apartment'])
    meter = await  orm_get_user_meters_last(session, user.tele_id)
    current_value = None
    name_meter = ''
    if action == "water_hot_kitchen":
        current_value = meter.water_hot_kitchen if meter else None
        name_meter = 'Горячая вода кухня'
    elif action == "water_cold_kitchen":
        current_value = meter.water_cold_kitchen if meter else None
        name_meter = 'Холодная вода кухня'
    elif action == "water_hot_bath":
        current_value = meter.water_hot_bath if meter else None
        name_meter = 'Горячая вода СУ'
    elif action == "water_cold_bath":
        current_value = meter.water_cold_bath if meter else None
        name_meter = 'Холодная вода СУ'

    msg = (
        f'{name_meter}\nТекущие показания - '
        f'{current_value if current_value else " не найдены."}'
        '\nВведите показания счётчика.'
    )
    await callback_query.message.answer(msg)
    await state.set_state(state_mapping[action])
    await callback_query.answer()


@user_private_admin_router.message(F.text, StateFilter('*'))
async def save_meter_cmd(message: types.Message,
                         session: AsyncSession,
                         state: FSMContext):

    current_state = await state.get_state()
    if not current_state or not current_state.startswith("ChangeMeter"):
        return  # Игнорируем, если не в нужном состоянии

    data = await state.get_data()
    apartment = data.get('apartment')
    if not apartment:
        await message.answer("Ошибка: квартира не выбрана.")
        await state.clear()
        return

    user = await orm_get_user_apartment(session, apartment)
    if not user:
        await message.answer("Пользователь не найден.")
        await state.clear()
        return

    # Получаем текущие показания за месяц (если есть)
    meter = await orm_get_user_meters_last(session, user.tele_id)

    # Определяем, какое поле обновляем
    water_hot_kitchen_data = None
    water_cold_kitchen_data = None
    water_hot_bath_data = None
    water_cold_bath_data = None

    meter_value = None

    if current_state == ChangeMeter.water_hot_kitchen.state:
        meter_value = meter.water_hot_kitchen if meter else None
        water_hot_kitchen_data = message.text
    elif current_state == ChangeMeter.water_cold_kitchen.state:
        meter_value = meter.water_cold_kitchen if meter else None
        water_cold_kitchen_data = message.text
    elif current_state == ChangeMeter.water_hot_bath.state:
        meter_value = meter.water_hot_bath if meter else None
        water_hot_bath_data = message.text
    elif current_state == ChangeMeter.water_cold_bath.state:
        meter_value = meter.water_cold_bath if meter else None
        water_cold_bath_data = message.text
    else:
        await message.answer("Неизвестное состояние.")
        return

    # Валидация
    validate = await validate_data_meter(message, state, message.text, meter_value)
    if not validate:
        return

    await orm_add_update_meter(
        session,
        user.tele_id,
        water_hot_kitchen=water_hot_kitchen_data,
        water_cold_kitchen=water_cold_kitchen_data,
        water_hot_bath=water_hot_bath_data,
        water_cold_bath=water_cold_bath_data,
    )

    await message.answer('✅ Показания сохранены.')

    await show_meter_info(message, session, state, apartment)
