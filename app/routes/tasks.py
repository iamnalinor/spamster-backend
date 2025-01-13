import csv
from io import BytesIO, StringIO
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import quote

from annotated_types import Ge
from fastapi import APIRouter, BackgroundTasks, UploadFile
from openpyxl import Workbook
from starlette.responses import Response

from app.actions.workspace import (
    get_workspace_email_config,
    mass_send,
    notify_roles_in_workspace,
)
from app.asserts import assert403, assert404, fail_4xx
from app.config import FILES_DIR
from app.deps import email_sender
from app.deps.email_sender import EmailSender, Message
from app.deps.tokens import UserDep
from app.logic import stages
from app.logic.stages import StagedModel, StageState
from app.repo.target import TargetRepoDep
from app.repo.tasks import TasksRepoDep
from app.repo.workspace import WorkspaceRepoDep
from app.schemas.tasks import (
    HistoryResponseModel,
    RejectReason,
    TaskCreateModel,
    TaskFileResponseModel,
    TaskResponseModel,
    TaskUpdateModel,
    UploadFilesResultModel,
)

router = APIRouter()


@router.get(
    "/workspaces/{workspace_id}/tasks",
    tags=["Tasks"],
    description="List all tasks within a workspace that the user has access to.",
    responses={
        200: {"description": "List of tasks successfully retrieved"},
        403: {"description": "User doesn't have access to this workspace"},
    },
)
async def get_tasks(
    workspace_id: int, user: UserDep, ws_repo: WorkspaceRepoDep, repo: TasksRepoDep
) -> list[TaskResponseModel]:
    assert403(ws_repo.has_access(workspace_id, user.id))
    tasks = repo.get_workspace_tasks(workspace_id)
    return tasks


@router.post(
    "/workspaces/{workspace_id}/tasks",
    tags=["Tasks"],
    description="Create a new task in the specified workspace.",
    responses={
        200: {"description": "Task successfully created"},
        403: {"description": "User doesn't have access to this workspace"},
    },
)
async def create_task(
    workspace_id: int,
    task_create: TaskCreateModel,
    user: UserDep,
    ws_repo: WorkspaceRepoDep,
    repo: TasksRepoDep,
) -> TaskResponseModel:
    assert403(ws_repo.has_access(workspace_id, user.id))

    new_task = repo.create_task(
        workspace_id=workspace_id,
        user_id=user.id,
        name=task_create.name,
        description=task_create.description,
        subject="",
        content="",
    )
    return new_task


@router.get(
    "/tasks/{task_id}",
    tags=["Tasks"],
    description="Retrieve details of a specific task.",
    responses={
        200: {"description": "Task details successfully retrieved"},
        403: {"description": "User doesn't have access to this workspace"},
        404: {"description": "Task not found"},
    },
)
async def get_task(
    task_id: int,
    user: UserDep,
    ws_repo: WorkspaceRepoDep,
    repo: TasksRepoDep,
) -> TaskResponseModel:
    task = repo.get_task(task_id)
    assert404(task, "Task not found")
    assert403(ws_repo.has_access(task.workspace_id, user.id))

    return TaskResponseModel.model_validate(task)


@router.put(
    "/tasks/{task_id}",
    tags=["Tasks"],
    description="Update an existing task's details.",
    responses={
        200: {"description": "Task successfully updated"},
        403: {"description": "User doesn't have access to modify this task"},
        404: {"description": "Task not found"},
    },
)
async def update_task(
    task_id: int,
    task_update: TaskUpdateModel,
    user: UserDep,
    ws_repo: WorkspaceRepoDep,
    repo: TasksRepoDep,
) -> TaskResponseModel:
    task = repo.get_task(task_id)
    assert404(task, "Task not found")
    assert403(ws_repo.has_access(task.workspace_id, user.id))

    update = {}
    for field in ["name", "description", "subject", "content"]:
        if (val := getattr(task_update, field)) is not None:
            update[field] = val

    task = repo.update_task(task_id, user.id, **update)
    return task


@router.delete(
    "/tasks/{task_id}",
    tags=["Tasks"],
    description="Delete a specific task.",
    responses={
        200: {"description": "Task successfully deleted"},
        403: {"description": "User doesn't have access to delete this task"},
        404: {"description": "Task not found"},
    },
)
async def delete_task(
    task_id: int,
    user: UserDep,
    ws_repo: WorkspaceRepoDep,
    repo: TasksRepoDep,
) -> bool:
    task = repo.get_task(task_id)
    assert404(task, "Task not found")
    assert403(ws_repo.has_access(task.workspace_id, user.id))

    return repo.delete_task(task_id)


@router.get(
    "/tasks/{task_id}/history",
    tags=["Task history"],
    description="Retrieve the change history for a specific task.",
    responses={
        200: {"description": "Task history successfully retrieved"},
        403: {"description": "User doesn't have access to this task"},
        404: {"description": "Task not found"},
    },
)
async def list_history(
    task_id: int, user: UserDep, ws_repo: WorkspaceRepoDep, repo: TasksRepoDep
) -> list[HistoryResponseModel]:
    task = repo.get_task(task_id)
    assert404(task, "Task not found")
    assert403(ws_repo.has_access(task.workspace_id, user.id))
    return list(
        map(HistoryResponseModel.model_validate, repo.get_task_history(task_id))
    )


@router.post(
    "/tasks/{task_id}/check/{stage_id}/{done_or_reject}",
    tags=["Task stages"],
    description="Mark a task stage as complete or rejected in the workflow.",
    responses={
        200: {"description": "Stage status successfully updated"},
        403: {"description": "User doesn't have permission to manage this stage"},
        404: {"description": "Task or stage not found"},
        409: {"description": "Previous stages not completed"},
    },
)
async def manage_task_stage(
    task_id: int,
    user: UserDep,
    ws_repo: WorkspaceRepoDep,
    repo: TasksRepoDep,
    stage_id: str,
    done_or_reject: Literal["done", "reject"],
    background_tasks: BackgroundTasks,
    reject_reason: str,
):
    task = repo.get_task(task_id)
    assert404(task, "Task not found")
    assert403(ws_repo.has_access(task.workspace_id, user.id))
    model = StagedModel.deserialize_from_checklist(task.checks, stages.TEMPLATES)
    try:
        if done_or_reject == "done":
            stages.mark_as_done(
                model,
                ws_repo.get_role(task.workspace_id, user.id),
                stage_id,
                lambda s1, s2, s3: _state_change_observer(
                    background_tasks, task.workspace, ws_repo, task, user, s1, s2, s3
                ),
            )
        else:
            stages.reject(
                model,
                ws_repo.get_role(task.workspace_id, user.id),
                stage_id,
                [reject_reason],
                lambda s1, s2, s3: _state_change_observer(
                    background_tasks, task.workspace, ws_repo, task, user, s1, s2, s3
                ),
            )
        repo.update_task(
            task_id,
            user.id,
            checks={
                key: stage.value
                for key, stage in model.serialize_to_checklist().items()
            },
        )
    except stages.StagePermissionError:
        fail_4xx(403, "no permission to manage this stage")
    except stages.StageNotFoundError:
        fail_4xx(404, "no stage found")
    except stages.DependenciesNotDoneError:
        fail_4xx(409, "not all previous stages completed")
    return {"status": "ok"}


def _state_change_observer(bg, workspace, ws_repo, task, user, stage, old, new):
    print(f"Mailing with {old} to {new}")
    print(stage.roles_for_stage)
    if old == StageState.NOT_STARTED and new == StageState.IN_PROGRESS:
        message = email_sender.Message(
            f"Task is available in {workspace.name}",
            f"New task is available for your role: {task.name}",
        )
        bg.add_task(
            notify_roles_in_workspace,
            ws_repo,
            workspace.id,
            [role.value for role in stage.roles_for_stage],
            message,
        )
    if old == StageState.DONE and new == StageState.IN_PROGRESS:
        message = email_sender.Message(
            f"Task is re-opened in {workspace.name}",
            f"Task {task.name} was rejected by {user.login}.",
        )
        bg.add_task(
            notify_roles_in_workspace,
            ws_repo,
            workspace.id,
            [role.value for role in stage.roles_for_stage],
            message,
        )


@router.get(
    "/tasks/{task_id}/reject-reasons/{stage_id}",
    tags=["Task stages"],
    description="Get possible rejection reasons for a specific stage.",
    responses={
        200: {"description": "Rejection reasons successfully retrieved"},
        403: {"description": "User doesn't have access to this task"},
        404: {"description": "Task or stage not found"},
    },
)
async def get_reject_reasons(
    task_id: int,
    user: UserDep,
    ws_repo: WorkspaceRepoDep,
    repo: TasksRepoDep,
    stage_id: str,
) -> list[RejectReason]:
    task = repo.get_task(task_id)
    assert404(task, "Task not found")
    assert403(ws_repo.has_access(task.workspace_id, user.id))
    model = StagedModel.deserialize_from_checklist(task.checks, stages.TEMPLATES)
    try:
        return [
            RejectReason(**reason)
            for reason in stages.get_reject_reasons(model, stage_id)
        ]
    except stages.StageNotFoundError:
        fail_4xx(404, "no stage found")


@router.get(
    "/tasks/{task_id}/files",
    tags=["Task files"],
    description="Get list of files for task.",
    responses={
        200: {"description": "List of files. Use ID to download the file."},
        403: {"description": "You don't have access to this task"},
        404: {"description": "Task not found"},
    },
)
async def get_files(
    task_id: int, repo: TasksRepoDep, user: UserDep, ws_repo: WorkspaceRepoDep
) -> list[TaskFileResponseModel]:
    task = repo.get_task(task_id)
    assert404(task, "Task not found")
    assert403(ws_repo.has_access(task.workspace_id, user.id))

    return [
        TaskFileResponseModel(id=k, name=Path(v).name)
        for k, v in enumerate(task.files or [])
    ]


@router.get(
    "/tasks/{task_id}/files/{file_id}",
    tags=["Task files"],
    description="Get file by id.",
    responses={
        200: {"description": "Downloads file"},
        403: {"description": "You don't have access to this task"},
        404: {"description": "Task or file not found"},
        410: {"description": "The file was deleted from the server"},
    },
)
async def get_file(
    task_id: int,
    file_id: Annotated[int, Ge(0)],
    user: UserDep,
    ws_repo: WorkspaceRepoDep,
    repo: TasksRepoDep,
) -> Response:
    task = repo.get_task(task_id)
    assert404(task, "Task not found")
    assert403(ws_repo.has_access(task.workspace_id, user.id))
    assert404(file_id < len(task.files), "no file with such id")

    file_name = task.files[file_id]
    file_path = FILES_DIR / file_name
    if not file_path.is_file():
        fail_4xx(410, "the file was deleted from the server")

    file_stream = BytesIO()
    blob = file_path.read_bytes()
    file_stream.write(blob)
    file_stream.seek(0)

    return Response(
        file_stream.getvalue(),
        headers={
            "Content-Disposition": f"attachment;filename*=UTF-8''{quote(file_name)}"
        },
    )


@router.delete(
    "/tasks/{task_id}/files/{file_id}",
    tags=["Task files"],
    description="Delete file by id.",
    responses={
        200: {"description": "File deleted"},
        403: {"description": "You don't have access to this task"},
        404: {"description": "Task not found/File not found"},
    },
)
async def delete_file(
    task_id: int,
    file_id: Annotated[int, Ge(0)],
    user: UserDep,
    ws_repo: WorkspaceRepoDep,
    repo: TasksRepoDep,
) -> bool:
    task = repo.get_task(task_id)
    assert404(task, "Task not found")
    assert403(ws_repo.has_access(task.workspace_id, user.id))
    assert404(file_id < len(task.files), "no file with such id")

    file_name = task.files[file_id]
    file_path = FILES_DIR / file_name

    assert404(file_path.is_file(), "file not found")

    file_path.unlink()
    task.files.pop(file_id)
    repo.set_files(task.id, task.files)

    return True


@router.patch(
    "/tasks/{task_id}/upload-file",
    tags=["Task files"],
    description="Upload files to task.",
    responses={
        200: {"description": "Files uploaded. Returns count of uploaded files"},
        403: {"description": "You don't have access to this task"},
        404: {"description": "Task not found"},
    },
)
async def upload_file(
    task_id: int,
    files: list[UploadFile],
    user: UserDep,
    ws_repo: WorkspaceRepoDep,
    repo: TasksRepoDep,
) -> UploadFilesResultModel:
    task = repo.get_task(task_id)
    assert404(task, "Task not found")
    assert403(ws_repo.has_access(task.workspace_id, user.id))

    fs = []

    for f in files:
        # additional validation for name
        file_name = Path(f.filename).name
        fs.append(file_name)

        data = await f.read()
        (FILES_DIR / file_name).write_bytes(data)

    repo.set_files(task_id, task.files + fs)
    return UploadFilesResultModel(count=len(fs))


@router.post(
    "/tasks/{task_id}/import-targets",
    tags=["Task targets"],
    description=(
        "Import target emails from CSV file. "
        "Emails must be placed in the 'email' column."
    ),
    responses={
        200: {
            "description": "All targets imported. Returns count of imported targets."
        },
        400: {
            "description": "Invalid CSV format. See detail json param for exact reason."
        },
        403: {"description": "You don't have access to this task."},
        404: {"description": "Task not found."},
    },
)
async def import_targets(
    task_id: int,
    user: UserDep,
    repo: TargetRepoDep,
    targets: UploadFile,
    task_repo: TasksRepoDep,
    ws_repo: WorkspaceRepoDep,
) -> int:
    task = task_repo.get_task(task_id)
    assert404(task, "Task not found")
    assert403(ws_repo.has_access(task.workspace_id, user.id))

    repo.delete_old_targets(task_id)

    # Convert bytes to string for csv reader
    try:
        content = targets.file.read().decode("utf-8")
        csvfile = StringIO(content)
        reader = csv.reader(csvfile, delimiter=";")
    except Exception:
        fail_4xx(400, "failed to read or decode the file")

    try:
        headers = next(reader)
    except StopIteration:
        fail_4xx(400, "empty CSV file")

    try:
        email_col = headers.index("email")
    except ValueError:
        fail_4xx(400, "file must contain email column")

    target_type = "email"
    count_imported = 0

    for i, row in enumerate(reader):
        try:
            email = row[email_col].strip()
            if not email:  # Skip empty emails
                continue
            repo.create_target(task_id, target_type, email)
            count_imported += 1
        except IndexError:
            fail_4xx(400, f"malformed csv row at index {i}")

    return count_imported


@router.get(
    "/tasks/{task_id}/export-targets",
    tags=["Task targets"],
    description="Download task targets as Excel file.",
    responses={
        200: {"description": ".xlsx file with task targets"},
        403: {"description": "Forbidden - no access to workspace"},
        404: {"description": "Task not found"},
    },
)
async def export_changes(
    task_id: int,
    user: UserDep,
    repo: TargetRepoDep,
    ws_repo: WorkspaceRepoDep,
    task_repo: TasksRepoDep,
):
    task = task_repo.get_task(task_id)
    assert404(task, "Task not found")
    assert403(ws_repo.has_access(task.workspace_id, user.id))

    # Create workbook and select active sheet
    wb = Workbook()
    ws = wb.active

    # Add headers
    ws.append(["ID", "Email"])

    # Add data rows
    targets = repo.get_by_task(task_id)
    for target in targets:
        ws.append([target.id, target.data])

    # Save to memory stream
    excel_stream = BytesIO()
    wb.save(excel_stream)
    excel_stream.seek(0)

    return Response(
        content=excel_stream.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=targets.xlsx"},
    )


@router.post(
    "/tasks/{task_id}/send",
    tags=["Task targets"],
    description="Send mail to task targets.",
    responses={
        200: {"description": "Mails sent"},
        403: {"description": "You don't have access to this task."},
        404: {"description": "Task not found."},
    },
)
def send_spam_mail(
    task_id: int,
    user: UserDep,
    repo: TargetRepoDep,
    task_repo: TasksRepoDep,
    ws_repo: WorkspaceRepoDep,
) -> bool:
    task = task_repo.get_task(task_id)
    assert404(task, "Task not found")
    assert403(ws_repo.has_access(task.workspace_id, user.id))

    targets = [t.data for t in repo.get_by_task(task_id)]
    mass_send(
        targets,
        EmailSender(get_workspace_email_config(ws_repo, task.workspace_id)),
        Message(title=task.subject, text=task.content),
    )
    task_repo.archive_task(task_id)
    return True
