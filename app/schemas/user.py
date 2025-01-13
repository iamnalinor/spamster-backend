from typing import Annotated

from pydantic import StringConstraints

from app.schemas import BaseSchema


class RegisterModel(BaseSchema):
    login: Annotated[str, StringConstraints(pattern=r"[a-zA-Z0-9-]{1,30}")]
    password: Annotated[str, StringConstraints(min_length=1)]
    name: Annotated[str, StringConstraints(min_length=1, max_length=30)]


class LoginModel(BaseSchema):
    login: str
    password: str


class JwtTokenModel(BaseSchema):
    access_token: str


class UserModel(BaseSchema):
    id: int
    name: str
    login: str
    email: str | None
