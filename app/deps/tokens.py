import secrets
from typing import Annotated, TypeAlias, cast

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError

from app.asserts import assert401, fail_4xx
from app.deps.database import SessionDep
from app.models.user import User


def issue_token(user_id: int, jwt_secret: str) -> str:
    encoded = jwt.encode(
        {"sub": user_id, "jti": secrets.token_hex()},
        jwt_secret,
        algorithm="HS256",
    )
    return encoded


def resolve_token_into_user(
    db: SessionDep,
    creds: Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())],
) -> User:
    try:
        unsafe_data = jwt.decode(creds.credentials, options={"verify_signature": False})
    except InvalidTokenError:
        fail_4xx(401)

    assert401("sub" in unsafe_data)

    user = db.query(User).filter(User.id == unsafe_data["sub"]).one_or_none()
    assert401(user)
    assert401(user.jwt_secret)

    try:
        data = jwt.decode(creds.credentials, key=user.jwt_secret, algorithms=["HS256"])
    except InvalidTokenError:
        fail_4xx(401)

    assert data["sub"] == user.id
    assert user is not None

    return cast(User, user)


UserDep: TypeAlias = Annotated[User, Depends(resolve_token_into_user)]
