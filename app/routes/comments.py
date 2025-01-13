from fastapi import APIRouter

from app.asserts import assert403, assert404
from app.deps.tokens import UserDep
from app.repo.tasks import TasksRepoDep
from app.repo.workspace import WorkspaceRepoDep
from app.schemas.comments import CreateTaskCommentModel, TaskCommentModel

router = APIRouter(tags=["Task comments"])


@router.post("/tasks/{task_id}/comments", description="Create a new comment on a task")
async def create_task_comment(
    task_id: int,
    comment: CreateTaskCommentModel,
    tasks_repo: TasksRepoDep,
    workspace_repo: WorkspaceRepoDep,
    current_user: UserDep,
) -> TaskCommentModel:
    task = tasks_repo.get_task(task_id)
    assert404(task, "Task not found")

    assert403(
        workspace_repo.has_access(task.workspace_id, current_user.id),
        "No access to this workspace",
    )

    return tasks_repo.create_comment(task_id, current_user.id, comment.text)


@router.get("/tasks/{task_id}/comments", description="Get all comments for a task")
async def get_task_comments(
    task_id: int,
    tasks_repo: TasksRepoDep,
    workspace_repo: WorkspaceRepoDep,
    current_user: UserDep,
) -> list[TaskCommentModel]:
    task = tasks_repo.get_task(task_id)
    assert404(task, "Task not found")

    assert403(
        workspace_repo.has_access(task.workspace_id, current_user.id),
        "No access to this workspace",
    )

    comments = []
    for comment in tasks_repo.get_task_comments(task_id):
        comments.append(
            TaskCommentModel(
                id=comment.id,
                user_id=comment.user_id,
                author=comment.user.login,
                task_id=comment.task_id,
                created_at=comment.created_at,
                text=comment.text,
            )
        )

    return comments
