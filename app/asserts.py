from typing import Any, Never

from fastapi import HTTPException

REASONS = {
    400: "bad request",
    401: "credentials are invalid or expired",
    403: "you can't access this resource",
    404: "resource not found",
    409: "conflict",
}


def fail_4xx(status_code: int, reason: str | None = None) -> Never:
    if not reason:
        reason = REASONS.get(status_code, f"failed with status {status_code}")

    raise HTTPException(
        status_code=status_code,
        detail=reason,
    )


def assert400(condition: Any, reason: str | None = None) -> None:
    if not condition:
        fail_4xx(400, reason)


def assert401(condition: Any, reason: str | None = None) -> None:
    if not condition:
        fail_4xx(401, reason)


def assert403(condition: Any, reason: str | None = None) -> None:
    if not condition:
        fail_4xx(403, reason)


def assert404(condition: Any, reason: str | None = None) -> None:
    if not condition:
        fail_4xx(404, reason)


def assert409(condition: Any, reason: str | None = None) -> None:
    if not condition:
        fail_4xx(409, reason)
