from fastapi import APIRouter

from app.deps.database import SessionDep

router = APIRouter(tags=["Ping"])


@router.get("/ping")
async def ping_route(db: SessionDep) -> bool:
    return True
