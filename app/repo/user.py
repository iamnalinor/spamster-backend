from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.deps.database import SessionDep
from app.models import User


class UserRepo:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, user_id: int) -> User | None:
        return self.session.query(User).filter(User.id == user_id).one_or_none()

    def get_by_login(self, login: str) -> User | None:
        return self.session.query(User).filter(User.login == login).one_or_none()

    def create(
        self, login: str, password_hash: str, password_salt: str, name: str
    ) -> User:
        user = User(
            login=login,
            password_hash=password_hash,
            password_salt=password_salt,
            name=name,
        )
        self.session.add(user)
        self.session.commit()
        return user

    def is_login_available(self, login: str) -> bool:
        return (
            self.session.query(User).filter(User.login == login).one_or_none() is None
        )


def get_user_repository(db: SessionDep) -> UserRepo:
    return UserRepo(db)


UserRepoDep = Annotated[UserRepo, Depends(get_user_repository)]
