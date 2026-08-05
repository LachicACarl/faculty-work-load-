from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend_api.core.database import Base


class WorkloadPolicy(Base):
    __tablename__ = "workload_policies"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    policy_name: Mapped[str] = mapped_column(String(255), nullable=False)
    max_teaching_units: Mapped[int] = mapped_column(Integer, nullable=False)
    overload_limit: Mapped[float] = mapped_column(Float, nullable=False)
