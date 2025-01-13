from sqlalchemy import Column, String, Text
from sqlalchemy.orm import Mapped, relationship, validates

from app.deps.database import Base
from app.utils import rand_string


class User(Base):
    __tablename__ = "users"

    login: Mapped[str] = Column(String(30), nullable=False, unique=True)
    name: Mapped[str] = Column(String(30), nullable=False)
    password_hash: Mapped[str] = Column(Text(), nullable=False)
    password_salt: Mapped[str] = Column(String(100), nullable=False)
    jwt_secret: Mapped[str] = Column(String(100), default=rand_string, nullable=False)
    workspaces = relationship("WorkspaceMembership", back_populates="user")
    email: Mapped[str] = Column(String(100), nullable=True, default=None)

    @validates("email")
    def check_email(self, key, value):
        if "@" not in value:
            raise ValueError("Invalid email")
        return value
