import os

from sqlalchemy.ext.asyncio import (create_async_engine,
                                    async_sessionmaker,
                                    AsyncSession)
from dbase.models import Base
from dbase.orm_query import orm_create_test_users, create_restrict_words_db

engine = create_async_engine(os.getenv('DATABASE_URL'), echo=True)
session_maker = async_sessionmaker(bind=engine,
                                   class_=AsyncSession,
                                   expire_on_commit=False)


async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_maker() as session:
        await orm_create_test_users(session)
        await create_restrict_words_db(session)

async def drop_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
