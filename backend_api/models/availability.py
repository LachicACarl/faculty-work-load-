from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from backend_api.core.database import Base


class Availability(Base):
    __tablename__ = "availability"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    faculty_id: Mapped[int] = mapped_column(ForeignKey("faculty.id"), nullable=False)
    day_of_week: Mapped[str] = mapped_column(String(20), nullable=False)
    time_slot: Mapped[str] = mapped_column(String(100), nullable=False)
