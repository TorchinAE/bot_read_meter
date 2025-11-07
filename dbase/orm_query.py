import logging
from datetime import datetime
from typing import Optional, Sequence, Union

from aiogram import Bot
from aiogram.types import DateTime
from sqlalchemy import delete, desc, extract, func, insert, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload


from common.test_users import test_users
from dbase.models import Meter, User, Words, BanUsers, Power
from handlers.const import NUMBER_TSJ

logger = logging.getLogger(__name__)


async def orm_create_test_users(session: AsyncSession):
    query = select(User)
    result = await session.execute(query)
    if result.first():
        return
    session.add_all(
        [
            User(
                name=user["name"],
                apartment=user["apartment"],
                phone=user["phone"],
                confirmed=user["confirmed"],
                tele_id=user["tele_id"],
            )
            for user in test_users
        ]
    )
    await session.commit()


async def create_restrict_words_db(
    session: AsyncSession,
):
    query = select(Words)
    result = await session.execute(query)
    words = result.scalars().first()
    if words:
        return
    restrict_words = set()
    with open("ban_words.txt", "r", encoding="utf-8") as f:
        for line in f:
            word = line.strip().lower()
            if word:
                restrict_words.add(word)
    words_to_add = [Words(word=word) for word in restrict_words]
    session.add_all(words_to_add)
    await session.commit()


async def orm_get_words(
    session: AsyncSession,
):
    query = select(Words)
    result = await session.execute(query)
    words = result.scalars().all()
    return [w.word for w in words]


async def change_restrict_word(
    session: AsyncSession, old_word: str, new_word: str
):
    try:
        change = await orm_get_word_obj(session, old_word)
        change.word = new_word
        await session.commit()
        return True
    except IntegrityError:
        await session.rollback()
        return False


async def orm_get_word_obj(session: AsyncSession, word: str):
    query = select(Words).where(Words.word == word)
    result = await session.execute(query)
    return result.scalars().first()


async def orm_del_word_obj(session: AsyncSession, word: Words):
    await session.delete(word)
    await session.commit()


async def orm_add_word(session: AsyncSession, word: str):
    try:
        query = insert(Words).values(word=word)
        await session.execute(query)
        await session.commit()
    except Exception as e:
        logger.warning(f'Ошибка добавления слова "{word}" {e}')


async def orm_add_user(
    session: AsyncSession,
    tele_id: int,
    name: Optional[str] = None,
    apartment: Optional[int] = None,
    phone: Optional[str] = None,
    confirmed: bool = False,
):
    query = select(User).where(User.tele_id == tele_id)
    result = await session.execute(query)
    user = result.scalars().first()
    if user is None:
        session.add(
            User(
                tele_id=tele_id,
                name=name,
                apartment=apartment,
                phone=phone,
                confirmed=confirmed,
            )
        )
    else:
        user.name = name or user.name
        user.apartment = apartment or user.apartment
        user.phone = phone or user.phone
        user.confirmed = confirmed
    await session.commit()


async def orm_get_user_from_apartment(
    session: AsyncSession, apartment: int
) -> User:
    query = select(User).where(
        User.apartment == apartment, User.confirmed.is_(True)
    )
    result = await session.execute(query)
    user = result.scalars().first()
    return user


async def orm_get_user_tele(session: AsyncSession, tele_id: int) -> User:
    query = select(User).where(User.tele_id == tele_id)
    result = await session.execute(query)
    user = result.scalars().first()
    return user


async def orm_get_users_confirm(session: AsyncSession) -> Sequence[User]:
    query = select(User).where(User.confirmed.is_(True))
    result = await session.execute(query)
    users = result.scalars().all()
    return users


async def orm_add_admins(
    session: AsyncSession, admin_tele_ids: list[int], chat_id, bot: Bot
) -> None:

    query = select(User).where(User.tele_id.in_(admin_tele_ids))
    result = await session.execute(query)
    existing_users_list = result.scalars().all()
    existing_users = {user.tele_id: user for user in existing_users_list}
    existing_users_set = set(existing_users.keys())
    admin_to_del = existing_users_set - set(admin_tele_ids)
    admin_to_add = set(admin_tele_ids) - existing_users_set

    for tele_id in admin_tele_ids:
        if tele_id in existing_users_set:
            existing_users[tele_id].admin = True

    for admin in existing_users_list:
        if admin.tele_id in admin_to_del:
            admin.admin = False
    for user in admin_to_add:
        chat_member = await bot.get_chat_member(chat_id, user)
        full_name = chat_member.user.full_name or f"Admin {user}"
        session.add(
            User(
                tele_id=user,
                name=full_name,
                apartment=NUMBER_TSJ,
                confirmed=True,
                admin=True,
            )
        )
    await session.commit()


async def orm_get_admin_list(session: AsyncSession) -> Sequence[User]:
    query = select(User).where(User.admin.is_(True))
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_users_to_apart(
    session: AsyncSession, start_apart: int, fnsh_apart: int
) -> list[User]:
    query = select(User).where(
        User.apartment >= start_apart,
        User.apartment <= fnsh_apart,
        User.confirmed.is_(True),
    )
    result = await session.execute(query)
    users = result.scalars().all()
    return list(users)


async def orm_del_user(session: AsyncSession, user_tele_id: int) -> bool:
    query = delete(User).where(User.tele_id == user_tele_id)
    result = await session.execute(query)
    await session.commit()
    return result.rowcount > 0


async def orm_get_phone(session: AsyncSession, phone: str) -> Union[str, None]:
    query = select(User).where(User.phone == phone)
    result = await session.execute(query)
    user = result.scalars().first()
    return user.phone if user else None


async def orm_get_user_apartment(session: AsyncSession, apartment: str) -> User:
    query = select(User).where(User.apartment == apartment)
    result = await session.execute(query)
    user = result.scalars().first()
    return user


async def orm_get_count_need_confirmed(session: AsyncSession) -> int:
    query = select(func.count(User.id)).where(User.confirmed.is_(False))
    result = await session.execute(query)
    return result.scalar_one()


async def orm_get_confirmed(session: AsyncSession, user_tele_id: int) -> bool:
    user = await orm_get_user_tele(session, user_tele_id)
    if user is None:
        return False
    return user.confirmed


async def orm_get_unconfirmed_user_last(session: AsyncSession) -> User:
    query = select(User).where(User.confirmed.is_(False))
    result = await session.execute(query)
    user = result.scalars().first()
    return user


async def orm_add_update_meter(
    session: AsyncSession,
    user_id: int,
    water_hot_bath: Optional[int] = None,
    water_cold_bath: Optional[int] = None,
    water_hot_kitchen: Optional[int] = None,
    water_cold_kitchen: Optional[int] = None,
):
    now = datetime.now()
    query = (
        select(Meter)
        .where(
            Meter.user_id == user_id,
            func.extract("year", Meter.created) == now.year,
            func.extract("month", Meter.created) == now.month,
        )
        .order_by(desc(Meter.created))
    )
    result = await session.execute(query)
    meter = result.scalars().first()
    if meter is None:
        session.add(
            Meter(
                user_id=user_id,
                water_hot_bath=water_hot_bath,
                water_cold_bath=water_cold_bath,
                water_hot_kitchen=water_hot_kitchen,
                water_cold_kitchen=water_cold_kitchen,
            )
        )
    else:
        meter.user_id = user_id or meter.user_id
        meter.water_hot_bath = water_hot_bath or meter.water_hot_bath
        meter.water_cold_bath = water_cold_bath or meter.water_cold_bath
        meter.water_hot_kitchen = water_hot_kitchen or meter.water_hot_kitchen
        meter.water_cold_kitchen = (
            water_cold_kitchen or meter.water_cold_kitchen
        )
    await session.commit()


async def orm_add_update_power(
    session: AsyncSession,
    apartment: int,
    t0: int,
    t1: int,
    t2: int,
) -> bool:
    try:
        now = datetime.now()
        query = (
            select(Power)
            .where(
                Power.apartment == apartment,
                func.extract("year", Power.created) == now.year,
                func.extract("month", Power.created) == now.month,
            )
            .order_by(desc(Power.created))
        )
        result = await session.execute(query)
        power = result.scalars().first()
        if power is None:
            session.add(
                Power(
                    apartment=apartment,
                    t0=t0,
                    t1=t1,
                    t2=t2,
                )
            )
        else:
            power.apartment = apartment
            power.t0 = t0
            power.t1 = t1
            power.t2 = t2
        await session.commit()
        return True
    except Exception:
        await session.rollback()
        return False


async def post_block_user(
    session: AsyncSession,
    user_tele_id: int,
    ban_admin_tele_id: int,
    chat_id: int,
    name_admin: str,
    reason: str,
    unblock_time: DateTime,
) -> int:
    try:
        ban = BanUsers(
            user_tele_id=user_tele_id,
            ban_admin_tele_id=ban_admin_tele_id,
            chat_id=chat_id,
            name_admin=name_admin,
            reason=reason[:255],  # защита от переполнения
            unblock_time=unblock_time,
        )
        session.add(ban)
        await session.commit()
        return ban.id
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error("SQLAlchemy error in post_block_user: %s", e)
        raise
    except Exception as e:
        await session.rollback()
        logger.exception("Unexpected error in post_block_user: %s", e)
        raise


async def get_block_users(session: AsyncSession) -> Sequence[BanUsers]:
    result = await session.execute(
        select(BanUsers).where(BanUsers.confirmed.is_(True))
    )
    return result.scalars().all()


async def get_block_obj(
    session: AsyncSession, id_block: int
) -> Optional[BanUsers]:
    return await session.get(BanUsers, id_block)


async def set_block(
    session: AsyncSession, id_block: int, set_bool: bool, unblock_time: DateTime
) -> None:
    query = (
        update(BanUsers)
        .where(BanUsers.id == id_block)
        .values(confirmed=set_bool, unblock_time=unblock_time)
    )
    result = await session.execute(query)
    if result.rowcount == 0:
        raise ValueError(f"BanUsers with id={id_block} not found")
    await session.commit()


async def remove_block_user(session: AsyncSession, user_tele_id: int):
    await session.execute(
        delete(BanUsers).where(BanUsers.user_tele_id == user_tele_id)
    )
    await session.commit()


async def remove_block_user_id(session: AsyncSession, id: int):
    await session.execute(delete(BanUsers).where(BanUsers.id == id))
    await session.commit()


################# METERS#######################################
async def orm_get_all_meters_to_month(session: AsyncSession) -> Sequence[Meter]:
    now = datetime.now()
    query = (
        select(Meter)
        .join(User)
        .options(joinedload(Meter.user))
        .where(
            extract("year", Meter.created) == now.year,
            extract("month", Meter.created) == now.month,
        )
        .order_by(User.apartment, desc(Meter.created))
    )
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_all_energy_to_month(session: AsyncSession) -> Sequence[Power]:
    now = datetime.now()
    query = (
        select(Power)
        .where(
            extract("year", Power.created) == now.year,
            extract("month", Power.created) == now.month,
        )
        .order_by(Power.apartment, desc(Power.created))
    )
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_user_meters_last(
    session: AsyncSession, user_id: int
) -> Optional[Meter]:

    query = (
        select(Meter)
        .where(Meter.user_id == user_id)
        .order_by(desc(Meter.created))
    )
    result = await session.execute(query)
    meter = result.scalars().first()
    return meter


async def orm_get_meter_from_user_month_year(
    session: AsyncSession,
    user_id: int,
    month: Union[int, None] = None,
    year: Union[int, None] = None,
) -> Union[Meter, None]:

    if month is None:
        month = datetime.now().month
    if year is None:
        year = datetime.now().year

    query = (
        select(Meter)
        .where(
            Meter.user_id == user_id,
            func.extract("year", Meter.created) == year,
            func.extract("month", Meter.created) == month,
        )
        .order_by(desc(Meter.created))
        .limit(1)
    )
    result = await session.execute(query)
    return result.scalars().first()
