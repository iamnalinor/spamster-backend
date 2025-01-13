import datetime
from typing import Annotated, Any

from pydantic import Field

from app.enums.rolejobs import RoleJob, RoleJobState
from app.schemas import BaseSchema


class TaskCreateModel(BaseSchema):
    name: Annotated[str, Field(description="Name of the task.")]
    description: Annotated[str, Field(description="Terms of reference of the task.")]


class TaskUpdateModel(BaseSchema):
    name: Annotated[str | None, Field(description="Name of the task.")] = None
    description: Annotated[
        str | None, Field(description="Terms of reference of the task.")
    ] = None
    subject: Annotated[
        str | None, Field(description="The subject of the mail to be sent to clients.")
    ] = None
    content: Annotated[str | None, Field(description="The content of the mail.")] = None


class TaskResponseModel(BaseSchema):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    workspace_id: int
    author_id: int
    name: Annotated[str, Field(description="Name of the task.")]
    description: Annotated[str, Field(description="Terms of reference of the task.")]
    subject: Annotated[
        str, Field(description="The subject of the mail to be sent to clients.")
    ]
    content: Annotated[str, Field(description="The content of the mail.")]
    checks: Annotated[
        dict[RoleJob, RoleJobState],
        Field(description="Mapping of status of sub-tasks."),
    ]


class HistoryResponseModel(BaseSchema):
    id: int
    created_at: datetime.datetime
    task_id: int
    prev: Annotated[dict[str, Any], Field(description="Values before update")]
    data: Annotated[
        dict[str, Any],
        Field(
            description=(
                "Values after update. "
                "It is guaranteed that keys of prev and data match"
            )
        ),
    ]
    author_id: int
    author_name: str


class RejectReason(BaseSchema):
    id: str
    name: str


class TaskFileResponseModel(BaseSchema):
    id: int
    name: str


class UploadFilesResultModel(BaseSchema):
    count: int
