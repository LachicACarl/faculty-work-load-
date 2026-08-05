from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend_api.core.database import Base


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    subject_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    units: Mapped[int] = mapped_column(Integer, nullable=False)
    required_specialization: Mapped[str] = mapped_column(String(255), nullable=False)
    minimum_class_size: Mapped[int] = mapped_column(Integer, nullable=False)
