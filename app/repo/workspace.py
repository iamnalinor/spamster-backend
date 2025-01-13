from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.deps.database import get_session
from app.enums import roles
from app.models import User
from app.models.workspace import Workspace, WorkspaceMembership


class WorkspaceRepo:
    def __init__(self, session: Session):
        self.session = session

    def find_by_user(self, user: User) -> list[WorkspaceMembership]:
        return user.workspaces

    def create(self, name: str, user: User) -> Workspace:
        obj = Workspace(owner_id=user.id, name=name)
        self.session.add(obj)
        self.session.commit()
        return obj

    def find_by_id(self, w_id: int) -> Workspace | None:
        stmt = select(Workspace).where(Workspace.id == w_id).limit(1)
        return self.session.scalar(stmt)

    def update_name(self, w_id: int, name: str) -> Workspace:
        stmt = update(Workspace).returning(Workspace).where(Workspace.id == w_id)
        stmt = stmt.values(name=name)
        result = self.session.execute(stmt)
        self.session.commit()
        return result.fetchone()[0]

    def delete(self, w_id: int) -> None:
        stmt = delete(Workspace).where(Workspace.id == w_id)
        self.session.execute(stmt)
        self.session.commit()

    def get_members(self, w_id: int) -> list[WorkspaceMembership]:
        stmt = select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == w_id
        )
        return self.session.scalars(stmt).all()

    def has_access(self, w_id: int, user_id: int) -> bool:
        stmt = (
            select(WorkspaceMembership)
            .where(
                WorkspaceMembership.workspace_id == w_id,
                WorkspaceMembership.user_id == user_id,
            )
            .limit(1)
        )
        return self.session.scalar(stmt) is not None

    def grant_access(self, w_id: int, user_id: int, role: roles.Role) -> None:
        membership = WorkspaceMembership(workspace_id=w_id, user_id=user_id, role=role)
        self.session.add(membership)
        self.session.commit()

    def revoke_access(self, w_id: int, user_id: int) -> None:
        stmt = delete(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == w_id,
            WorkspaceMembership.user_id == user_id,
        )
        self.session.execute(stmt)
        self.session.commit()

    def get_role(self, w_id: int, user_id: int) -> roles.Role:
        stmt = (
            select(WorkspaceMembership)
            .where(
                WorkspaceMembership.workspace_id == w_id,
                WorkspaceMembership.user_id == user_id,
            )
            .limit(1)
        )
        return self.session.scalar(stmt).role


def get_workspace_repository(
    session: Session = Depends(get_session),
) -> Iterator[WorkspaceRepo]:
    yield WorkspaceRepo(session)


WorkspaceRepoDep = Annotated[WorkspaceRepo, Depends(get_workspace_repository)]
