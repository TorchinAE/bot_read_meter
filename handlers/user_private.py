from aiogram import F, Router, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from dbase.orm_query import orm_add_user, orm_get_phone, orm_get_user_tele
from filters.chat_types import ChatTypeFilter
from handlers.const import APARTMENTCOUNT
from handlers.states import AddUser
from kbds.kbds import get_user_main_btns

user_private_router = Router()
user_private_router.message.filter(ChatTypeFilter(["private"]))


@user_private_router.message(Command("menu"))
async def nemu_cmd(message: types.Message, session: AsyncSession):
    await start_cmd(message, session)


@user_private_router.message(Command("about"))
async def about_cmd(message: types.Message):
    text_mgs = (
        f"Приветствую Вас, {message.from_user.username}!\n"
        "Это бот для жителей дома №6 мкр. Рождественский."
        "\nДля начала работы отправьте команду /menu"
    )
    await message.answer(text_mgs)


@user_private_router.message(CommandStart())
@user_private_router.callback_query(F.data == "start")
async def start_cmd(message: types.Message, session: AsyncSession):
    text_mgs = (
        f"Приветствую Вас, {message.from_user.username}!\n"
        "Это бот для жителей дома №6 мкр. Рождественский.\n"
        "К сожалению, Вы не авторизированы как житель дома №6.\n"
    )

    user = await orm_get_user_tele(session, message.from_user.id)
    if user is None:
        text_mgs += (
            "Не смог найти Вас в базе.\n"
            "Давайте заполним данные, чтобы обратиться к Администратору"
            " чата за авторизацией."
        )

        btns = {"Заполнить данные": "insert_data_user", "Нет, спасибо": "cancel_data"}
    else:
        text_mgs += "О! Вижу ты тут не в первой. Будешь уточнять свои данные?"

        btns = {"Уточнить данные": "edit_data_user", "Нет, спасибо": "cancel_data"}
    await message.answer(text_mgs, reply_markup=get_user_main_btns(btns))


@user_private_router.callback_query(F.data == "insert_data_user")
async def add_user(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer(
        "Введите Ваше имя", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(AddUser.name)
    await callback_query.answer()


@user_private_router.callback_query(F.data == "edit_data_user")
async def add_user(
    callback_query: types.CallbackQuery, state: FSMContext, session: AsyncSession
):
    await callback_query.message.answer(
        "Хорошо, давайте отредактируем "
        "Ваши данные. "
        "\nДля сохранения текущего занчения "
        'введите "." (точку)',
        reply_markup=types.ReplyKeyboardRemove(),
    )
    user = await orm_get_user_tele(session=session, tele_id=callback_query.from_user.id)
    await callback_query.message.answer(f"Текущее имя {user.name}. Введите имя")
    await state.set_state(AddUser.name)
    await callback_query.answer()


@user_private_router.message(AddUser.name, F.text)
async def add_name(message: types.Message, state: FSMContext, session: AsyncSession):
    user = await orm_get_user_tele(session=session, tele_id=message.from_user.id)
    if message.text == "." and user:
        await state.update_data(name=user.name)
    else:
        await state.update_data(name=message.text)
    if user:
        await message.answer(f"Ваш номер квартиры {user.apartment}")
    await message.answer(
        "Введите номер квартиры", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(AddUser.apartment)


@user_private_router.message(AddUser.apartment, F.text)
async def add_apartment(
    message: types.Message, state: FSMContext, session: AsyncSession
):
    user = await orm_get_user_tele(session=session, tele_id=message.from_user.id)
    if message.text == "." and user:
        await state.update_data(apartment=user.apartment)
    else:
        if not message.text.isdigit() or not (0 < int(message.text) <= APARTMENTCOUNT):
            await message.answer(
                "Не корректный ввод номера квартиры. " "Такой квартиры в доме нет."
            )
            return
        await state.update_data(apartment=message.text)
    if user:
        await message.answer(f"Ваш номер телефона {user.phone}")
    await message.answer(
        "Введите телефон в формате +7ХХХХХХХХХХ",
        reply_markup=types.ReplyKeyboardRemove(),
    )
    await state.set_state(AddUser.phone)


@user_private_router.message(AddUser.phone, F.text)
async def add_phone(message: types.Message, state: FSMContext, session: AsyncSession):
    user = await orm_get_user_tele(session=session, tele_id=message.from_user.id)
    if message.text == "." and user:
        await state.update_data(phone=user.phone)
    else:
        phone = message.text
        if not phone.startswith("+7") or len(phone) != 12 or not phone[1:].isdigit():
            await message.answer(
                "Не корректный формат телефона. "
                "Введите телефон в формате +7ХХХХХХХХХХ"
            )
            return
        if await orm_get_phone(session=session, phone=phone):
            await message.answer(f"Номер телефона {phone} уже занят, " "введите другой")
            return
        await state.update_data(phone=message.text)
    data = await state.get_data()
    await orm_add_user(session=session, tele_id=message.from_user.id, **data)
    await message.answer(
        "Спасибо, данные добавлены. Обратитесь "
        "к Администратору для подтверждения данных",
        reply_markup=types.ReplyKeyboardRemove(),
    )
    await state.clear()


@user_private_router.callback_query(F.data == "cancel_data")
async def cancel_cmd(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer("Вы отменили операцию.")
    await state.clear()
    await callback_query.message.answer("Был рад пообщаться.")


@user_private_router.callback_query()
async def debug_all_callbacks(callback_query: types.CallbackQuery):
    print(f"Получен callback_data в user_private_router:'" f"{callback_query.data}")
    await callback_query.answer("Обработка не найдена для: " + callback_query.data)
