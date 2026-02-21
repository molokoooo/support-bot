from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.database.sql_engine import Base

class About(Base):
    __tablename__ = 'about'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(25), nullable=False)
    link: Mapped[str] = mapped_column(nullable=False)
