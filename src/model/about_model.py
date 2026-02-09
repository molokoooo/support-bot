from datetime import datetime
from typing import List, Optional, Any, Dict

from sqlalchemy import String, ForeignKey, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.sql_engine import Base

class About(Base):
    __tablename__ = 'about'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    link: Mapped[str] = mapped_column(nullable=False)
