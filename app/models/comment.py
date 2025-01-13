from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.deps.database import Base


class TaskComment(Base):
    __tablename__ = "comments"

    task_id: Mapped[int] = mapped_column(
        "task_id", ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    task = relationship("Task")

    user_id: Mapped[int] = mapped_column(
        "user_id", ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    user = relationship("User")

    text: Mapped[str] = mapped_column("text", String(), nullable=False)

    @property
    def author(self):
        return self.user.name
