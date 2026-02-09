from datetime import datetime
from typing import List, Optional, Any, Dict

from sqlalchemy import String, ForeignKey, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.sql_engine import Base

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[str]
    role: Mapped[str] = mapped_column(
        Enum(
            "SuperAdmin", "Admin", "FAQ", "Support", "User",
            name="user_role_enum"
        ),
        default="User"
    )
    # SuperAdmin - САМЫЙ ГЛАВНЫЙ АДМИН
    # ADMIN - АДМИН ОТВЕЧАЮЩИЙ ЗА САПОРТ И FAQ
    # FAQ - ОТВЕЧАЕТ ЗА FAQ
    # SUPPORT - ОТВЕЧАЕТ ЗА ТЕХ ПОДДЕРЖКУ
    # USER - ОБЫЧНЫЙ ПОЛЬЗОВАТЕЛЬ

    tickets: Mapped[str] = relationship("Ticket", back_populates="user")


class Ticket(Base):
    __tablename__ = 'tickets'

    id: Mapped[int] = mapped_column(primary_key=True)
    media: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True) # URL MEDIA
    content: Mapped[str] = mapped_column(String(1024))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    date: Mapped[datetime] = mapped_column(default=datetime.now())
    state: Mapped[str] = mapped_column(
        Enum(
            "open", "closed",
            name="state_enum",
        ),
        default="open"
    )
    # STATE - ЗАКРЫВАТЬ ДОЛЖЕН ПОЛЬЗОВАТЕЛЬ, ЕСЛИ ЗАКРЫТ ТО ДОЛЖЕН УДАЛЯТЬ ЧЕРЕЗ 24 ЧАСА

    user: Mapped[User] = relationship("User", back_populates="tickets")

