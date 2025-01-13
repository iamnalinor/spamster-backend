from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.deps.database import Base
from app.enums import roles


class Workspace(Base):
    __tablename__ = "workspaces"

    owner_id: Mapped[int] = mapped_column(
        "owner_id", ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    owner = relationship("User")

    name: Mapped[str] = mapped_column("name", String(), nullable=False)

    smtp_host: Mapped[str] = mapped_column("smtp_host", String(), nullable=True)
    smtp_port: Mapped[int] = mapped_column("smtp_port", Integer(), nullable=True)
    smtp_email: Mapped[str] = mapped_column("smtp_email", String(), nullable=True)
    smtp_password: Mapped[str] = mapped_column("smtp_password", String(), nullable=True)


class WorkspaceMembership(Base):
    __tablename__ = "memberships"

    user_id: Mapped[int] = mapped_column(
        "user_id", ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    user = relationship("User", back_populates="workspaces")

    workspace_id: Mapped[int] = mapped_column(
        "workspace_id", ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    workspace = relationship("Workspace")

    role: Mapped[roles.Role] = mapped_column("role", Enum(roles.Role), nullable=False)
