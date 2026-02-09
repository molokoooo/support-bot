from typing import List

from sqlalchemy.orm import Mapped, mapped_column

from src.database.sql_engine import Base

class FAQ(Base):
    __tablename__ = 'faq'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)
    media: Mapped[List] = mapped_column(nullable=True)
