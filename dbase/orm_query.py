from email.policy import default
from typing import Optional

from sqlalchemy import select, Boolean
from sqlalchemy.ext.asyncio import AsyncSession

from common.test_users import test_users
from dbase.models import User

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

async def orm_get_phone(session: AsyncSession, phone:str) -> str:
    query = select(User).where(User.phone == phone)
    result = await session.execute(query)
    user =result.scalars().first()
    return user.phone is not None

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


