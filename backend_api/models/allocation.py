from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from backend_api.core.database import Base


class Allocation(Base):
    __tablename__ = "allocations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    faculty_id: Mapped[int] = mapped_column(ForeignKey("faculty.id"), nullable=False)
    section_id: Mapped[int] = mapped_column(ForeignKey("sections.id"), nullable=False)
    justification: Mapped[str] = mapped_column(String(500), nullable=False)
