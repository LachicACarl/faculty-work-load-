from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from backend_api.core.database import Base


class Faculty(Base):
    __tablename__ = "faculty"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    employee_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    department: Mapped[str] = mapped_column(String(255), nullable=False)
    employment_type: Mapped[str] = mapped_column(String(100), nullable=False)
    tenure_status: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
