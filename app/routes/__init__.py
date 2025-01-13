from fastapi import APIRouter

from ..misc import app
from . import comments, ping, tasks, user, workspace

root_router = APIRouter(prefix="/api")
root_router.include_router(ping.router)
root_router.include_router(user.router)
root_router.include_router(workspace.router)
root_router.include_router(tasks.router)
root_router.include_router(comments.router)

app.include_router(root_router)
