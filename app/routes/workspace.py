from fastapi import APIRouter

from app.asserts import assert400, assert403, assert404
from app.deps.tokens import UserDep
from app.repo.user import UserRepoDep
from app.repo.workspace import WorkspaceRepoDep
from app.schemas.user import UserModel
from app.schemas.workspace import (
    WorkspaceCreateModel,
    WorkspaceGrantAccessModel,
    WorkspaceMemberModel,
    WorkspaceResponseModel,
    WorkspaceRevokeAccessModel,
    WorkspaceUpdateModel,
)

router = APIRouter(tags=["Workspace"])


@router.post(
    "/workspaces",
    response_model=WorkspaceResponseModel,
    description="Create a new workspace",
    responses={
        200: {"description": "Workspace created successfully"},
    },
)
def create_workspace(
    data: WorkspaceCreateModel,
    user: UserDep,
    repo: WorkspaceRepoDep,
):
    workspace = repo.create(name=data.name, user=user)
    repo.grant_access(workspace.id, user.id, data.my_role)
    return workspace


@router.get(
    "/workspaces",
    response_model=list[WorkspaceResponseModel],
    description="List all workspaces owned by the authenticated user",
    responses={
        200: {"description": "List of workspaces returned successfully"},
    },
)
def list_workspaces(
    user: UserDep,
    repo: WorkspaceRepoDep,
):
    memberships = repo.find_by_user(user)
    return [membership.workspace for membership in memberships]


@router.get(
    "/workspaces/{workspace_id}",
    response_model=WorkspaceResponseModel,
    description="Get workspace by ID",
    responses={
        200: {"description": "Workspace returned successfully"},
        403: {"description": "Not authorized to access this workspace"},
        404: {"description": "Workspace not found"},
    },
)
def get_workspace(
    workspace_id: int,
    user: UserDep,
    repo: WorkspaceRepoDep,
):
    workspace = repo.find_by_id(workspace_id)
    assert404(workspace)
    assert403(repo.has_access(workspace_id, user.id))
    return workspace


@router.put(
    "/workspaces/{workspace_id}",
    response_model=WorkspaceResponseModel,
    description="Update workspace name. You must be owner to call this method.",
    responses={
        200: {"description": "Workspace updated successfully"},
        403: {"description": "Not authorized to modify this workspace"},
        404: {"description": "Workspace not found"},
    },
)
def update_workspace(
    workspace_id: int,
    data: WorkspaceUpdateModel,
    user: UserDep,
    repo: WorkspaceRepoDep,
):
    workspace = repo.find_by_id(workspace_id)
    assert404(workspace)
    assert403(workspace.owner_id == user.id)
    return repo.update_name(workspace_id, data.name)


@router.post(
    "/workspaces/{workspace_id}/grantAccess",
    description="Grant access to user by login. You must be owner to call this method.",
    responses={
        200: {"description": "Access granted successfully"},
        400: {"description": "Invalid user login"},
        403: {"description": "Not authorized to modify this workspace"},
        404: {"description": "Workspace not found"},
    },
)
def grant_access(
    workspace_id: int,
    data: WorkspaceGrantAccessModel,
    user: UserDep,
    repo: WorkspaceRepoDep,
    user_repo: UserRepoDep,
) -> bool:
    target_user = user_repo.get_by_login(data.login)
    assert400(target_user is not None, "no user with such login")
    workspace = repo.find_by_id(workspace_id)
    assert404(workspace)
    assert403(workspace.owner_id == user.id)

    assert400(
        not repo.has_access(workspace.id, target_user.id),
        "User already has access to this workspace",
    )

    repo.grant_access(workspace_id, target_user.id, data.role)
    return True


@router.post(
    "/workspaces/{workspace_id}/revokeAccess",
    description="Revoke access to user by login. You must be owner to call this method",
    responses={
        200: {"description": "Access revoked successfully"},
        400: {"description": "Invalid user login"},
        403: {"description": "Not authorized to modify this workspace"},
        404: {"description": "Workspace not found"},
    },
)
def revoke_access(
    workspace_id: int,
    data: WorkspaceRevokeAccessModel,
    user: UserDep,
    repo: WorkspaceRepoDep,
    user_repo: UserRepoDep,
) -> bool:
    target_user = user_repo.get_by_login(data.login)
    assert400(target_user is not None, "no user with such login")
    assert400(target_user.id != user.id, "you can't revoke access from yourself")
    workspace = repo.find_by_id(workspace_id)
    assert404(workspace)
    assert403(workspace.owner_id == user.id)
    assert404(repo.has_access(workspace_id, target_user.id), "no such member found")
    repo.revoke_access(workspace_id, target_user.id)
    return True


@router.get(
    "/workspaces/{workspace_id}/members",
    description="Get all members of a workspace",
    responses={
        200: {"description": "List of workspace members returned successfully"},
        403: {"description": "Not authorized to view this workspace"},
        404: {"description": "Workspace not found"},
    },
)
def get_members(
    workspace_id: int,
    user: UserDep,
    repo: WorkspaceRepoDep,
) -> list[WorkspaceMemberModel]:
    workspace = repo.find_by_id(workspace_id)
    assert404(workspace)
    assert403(repo.has_access(workspace_id, user.id))

    response = [
        WorkspaceMemberModel(
            user=UserModel.model_validate(member.user),
            role=member.role,
            is_owner=(member.user_id == workspace.owner_id),
        )
        for member in repo.get_members(workspace_id)
    ]
    return response
