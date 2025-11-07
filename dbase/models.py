from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tele_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    apartment: Mapped[int] = mapped_column(Integer, nullable=True)
    phone: Mapped[str] = mapped_column(String(13), nullable=True, unique=True)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    admin: Mapped[bool] = mapped_column(Boolean, default=False)
    meters: Mapped[list["Meter"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    ban_records: Mapped[list["BanUsers"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Power(Base):
    __tablename__ = 'power'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    apartment: Mapped[int] = mapped_column(Integer, nullable=False)
    t0: Mapped[int] = mapped_column(Integer, nullable=True)
    t1: Mapped[int] = mapped_column(Integer, nullable=True)
    t2: Mapped[int] = mapped_column(Integer, nullable=True)

    def __repr__(self):
        return (
            f'{self.apartment} кв: T0 - {self.t0}, '
            f'T1 - {self.t1}, T2 - {self.t2}'
        )


class Meter(Base):
    __tablename__ = "meter"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    water_hot_bath: Mapped[int] = mapped_column(Integer, nullable=True)
    water_cold_bath: Mapped[int] = mapped_column(Integer, nullable=True)
    water_hot_kitchen: Mapped[int] = mapped_column(Integer, nullable=True)
    water_cold_kitchen: Mapped[int] = mapped_column(Integer, nullable=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    user: Mapped["User"] = relationship(back_populates="meters")

    def __repr__(self):
        return (
            f"<Meter(id={self.id}, "
            f"created={self.created.strftime('%d.%m.%Y') if self.created else 'N/A'}, "
            f"water_hot_kitchen={self.water_hot_kitchen}, "
            f"water_cold_kitchen={self.water_cold_kitchen}, "
            f"water_hot_bath={self.water_hot_bath}, "
            f"water_cold_bath={self.water_cold_bath})>"
        )


class Words(Base):
    __tablename__ = "words"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    word: Mapped[str] = mapped_column(String, nullable=False, unique=True)


class BanUsers(Base):
    __tablename__ = "banned_users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_tele_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ban_admin_tele_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    name_admin: Mapped[str] = mapped_column(String(64), nullable=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    unblock_time: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    confirmed: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
    user: Mapped["User"] = relationship(back_populates="ban_records")
