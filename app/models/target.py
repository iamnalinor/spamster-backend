from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.deps.database import Base


class Target(Base):
    __tablename__ = "targets"

    task_id: Mapped[int] = mapped_column(
        "task_id", ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    task = relationship("Task")

    type: Mapped[str] = mapped_column("type", String(), nullable=False)
    data: Mapped[str] = mapped_column("data", String(), nullable=False)
