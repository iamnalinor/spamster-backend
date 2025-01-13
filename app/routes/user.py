from fastapi import APIRouter

from app.asserts import assert400, assert401, assert409
from app.deps.database import SessionDep
from app.deps.tokens import UserDep, issue_token
from app.repo.user import UserRepoDep
from app.schemas.user import JwtTokenModel, LoginModel, RegisterModel, UserModel
from app.utils import hash_password, rand_string

router = APIRouter(tags=["User"])


@router.post(
    "/user/register",
    description="Register user.",
    responses={
        200: {"description": "User registered successfully, returns auth token"},
        409: {"description": "User with such login already exists"},
    },
)
async def register_user(user_repo: UserRepoDep, model: RegisterModel) -> JwtTokenModel:
    assert409(
        user_repo.is_login_available(model.login),
        "login conflicts with another user",
    )

    password_salt = rand_string()
    password_hash = hash_password(model.password, password_salt)

    user_repo.create(
        login=model.login,
        password_hash=password_hash,
        password_salt=password_salt,
        name=model.name,
    )

    return await login_user(
        user_repo,
        LoginModel(
            login=model.login,
            password=model.password,
        ),
    )


@router.post("/user/login", description="Retrieve auth token.")
async def login_user(user_repo: UserRepoDep, model: LoginModel) -> JwtTokenModel:
    user = user_repo.get_by_login(model.login)
    assert401(user)

    password_hash = hash_password(model.password, user.password_salt)
    assert401(user.password_hash == password_hash)

    token = issue_token(user.id, user.jwt_secret)
    return JwtTokenModel(access_token=token)


@router.get("/user/me", description="Get me.")
async def get_me(user: UserDep) -> UserModel:
    return UserModel.model_validate(user)


@router.patch("/account/set-notification-email")
async def set_notification_email(
    email: str, user: UserDep, db: SessionDep
) -> UserModel:
    assert400("@" in email, "email is invalid")
    user.email = email
    db.add(user)
    db.commit()
    return UserModel(
        id=user.id,
        name=user.name,
        login=user.login,
        email=user.email,
    )
