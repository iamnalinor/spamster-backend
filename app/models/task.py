from sqlalchemy import JSON, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.deps.database import Base


class Task(Base):
    __tablename__ = "tasks"

    workspace_id: Mapped[int] = mapped_column(
        "workspace_id", ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    workspace = relationship("Workspace")

    author_id: Mapped[int] = mapped_column(
        "author_id", ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    author = relationship("User")

    name: Mapped[str] = mapped_column("name", String(), nullable=False)
    description: Mapped[str] = mapped_column("description", String(), nullable=False)

    subject: Mapped[str] = mapped_column("subject", String(), nullable=False)
    content: Mapped[str] = mapped_column("content", String(), nullable=False)

    checks: Mapped[dict] = mapped_column(JSON(), nullable=False)

    files: Mapped[list] = mapped_column(JSON(), nullable=True, default=lambda: [])

    is_archived: Mapped[bool] = mapped_column("is_archived", Boolean(), default=False)


class TaskUpdateEvent(Base):
    __tablename__ = "task_update_events"

    task_id: Mapped[int] = mapped_column(
        "task_id", ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    task = relationship("Task")

    author_id: Mapped[int] = mapped_column(
        "author_id", ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    author = relationship("User")

    @property
    def author_name(self):
        return self.author.name

    prev: Mapped[dict] = mapped_column("prev", JSON(), nullable=False)
    data: Mapped[dict] = mapped_column("data", JSON(), nullable=False)
