from sqlalchemy import DateTime, ForeignKey, String, func, Integer, Boolean, BigInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

class User(Base):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tele_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    apartment: Mapped[int] = mapped_column(Integer, nullable=True)
    phone: Mapped[str] = mapped_column(String(13), nullable=True, unique=True)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)

class Meter(Base):
    __tablename__ = 'meter'

    id :Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    water_hot_bath : Mapped[int] = mapped_column(Integer, nullable=True)
    water_cold_bath: Mapped[int] = mapped_column(Integer, nullable=True)
    water_hot_kitchen: Mapped[int] = mapped_column(Integer, nullable=True)
    water_cold_kitchen: Mapped[int] = mapped_column(Integer, nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id',ondelete='CASCADE'), nullable=False)

    user: Mapped['User'] = relationship(backref='meters')
