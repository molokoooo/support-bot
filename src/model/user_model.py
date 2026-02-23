from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import ForeignKey, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.sql_engine import Base

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[str] = mapped_column(unique=True)
    username: Mapped[str]
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
    user_message_id: Mapped[list] = mapped_column(JSONB, nullable=False)
    admin_message: Mapped[str] = mapped_column(nullable=True)
    user_telegram_id: Mapped[str] = mapped_column(ForeignKey("users.telegram_id"), unique=True)
    open_date: Mapped[datetime] = mapped_column(default=datetime.now())
    close_date: Mapped[datetime] = mapped_column(nullable=True)
    state: Mapped[str] = mapped_column(
        Enum("open", "processing", "closed", name="state_enum"),
        default="open"
    )
# STATE - ЗАКРЫВАТЬ ДОЛЖЕН АДМИН, ЕСЛИ ЗАКРЫТ ТО ДОЛЖЕН УДАЛЯТЬ ЧЕРЕЗ 24 ЧАСА, ЕСЛИ В PROCESSING 48 часов то тикет зарывается и удаляется

    user: Mapped[User] = relationship("User", back_populates="tickets")

