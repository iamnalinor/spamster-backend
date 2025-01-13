import datetime
from typing import Annotated

from pydantic import StringConstraints

from app.schemas import BaseSchema


class CreateTaskCommentModel(BaseSchema):
    text: Annotated[str, StringConstraints(min_length=1)]


class TaskCommentModel(BaseSchema):
    id: int
    task_id: int
    user_id: int
    author: str
    text: str
    created_at: datetime.datetime
