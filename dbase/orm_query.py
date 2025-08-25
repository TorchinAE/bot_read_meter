from datetime import datetime
from typing import Optional, Union, Sequence

from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from common.test_users import test_users
from dbase.models import User, Meter


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
            User(tele_id=tele_id, name=name, apartment=apartment, phone=phone, confirmed=confirmed)
        )
    else:
        user.name = name or user.name
        user.apartment = apartment or user.apartment
        user.phone = phone or user.phone
        user.confirmed = confirmed
    await session.commit()


async def orm_create_test_users(session: AsyncSession):
    query = select(User)
    result = await session.execute(query)
    if result.first():
        return
    session.add_all([User(
        name=user['name'],
        apartment=user['apartment'],
        phone=user['phone'],
        confirmed=user['confirmed'],
        tele_id=user['tele_id']
    ) for user in test_users])

    await session.commit()

async def orm_get_user(session: AsyncSession, user_id:int) -> User:
    query = select(User).where(User.tele_id == user_id)
    result = await session.execute(query)
    user = result.scalars().first()
    return user

async def orm_get_phone(session: AsyncSession, phone:str) ->  Union[str, None]:
    query = select(User).where(User.phone == phone)
    result = await session.execute(query)
    user =result.scalars().first()
    return user.phone if user else None

async def orm_get_apartment(session: AsyncSession, apartment:str) -> int:
    query = select(User).where(User.apartment == apartment)
    result = await session.execute(query)
    user =result.scalars().first()
    return user.apartment is not None

async def orm_get_confirmed(session: AsyncSession, user_id: int) -> bool:
    user = await orm_get_user(session, user_id)
    if user is None:
        return False
    return user.confirmed


async def orm_add_update_meter(
    session: AsyncSession,
    user_id: int,
    water_hot_bath: Optional[int] = None,
    water_cold_bath: Optional[int] = None,
    water_hot_kitchen: Optional[int] = None,
    water_cold_kitchen: Optional[int] = None,
):
    now = datetime.now()
    query = select(Meter).where(
        Meter.user_id == user_id,
        func.extract('year', Meter.created) == now.year,
        func.extract('month', Meter.created) == now.month
    ).order_by(desc(Meter.created))
    result = await session.execute(query)
    meter = result.scalars().first()
    if meter is None:
        session.add(
            Meter(user_id=user_id,
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
        meter.water_cold_kitchen = water_cold_kitchen or meter.water_cold_kitchen
    await session.commit()


async def orm_get_user_meters(session: AsyncSession, user_id: int) ->  Sequence[Meter]:
    query = select(Meter).where(Meter.user_id == user_id).order_by(desc(Meter.created))
    result = await session.execute(query)
    return result.scalars().all()

async def orm_get_user_meters_last(session: AsyncSession, user_id: int) -> Optional[Meter]:
    query = select(Meter).where(Meter.user_id == user_id).order_by(desc(Meter.created))
    result = await session.execute(query)
    meter = result.scalars().first()
    return meter

async def orm_get_meter_from_user_month_year(
        session: AsyncSession,
        user_id: int,
        month:  Union[int, None] = None,
        year: Union[int, None] = None,
)->  Union[Meter, None]:

    if month is None:
        month = datetime.now().month
    if year is None:
        year = datetime.now().year

    query = (select(Meter).where(
            Meter.user_id == user_id,
                func.extract('year', Meter.created) == year,
                func.extract('month', Meter.created) == month)
             .order_by(desc(Meter.created))
             .limit(1)
    )
    result = await session.execute(query)
    return result.scalars().first()
