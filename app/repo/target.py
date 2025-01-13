from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.deps.database import SessionDep
from app.models import Target


class TargetRepo:
    def __init__(self, session: Session):
        self.session = session

    def create_target(self, task_id, data_type, data) -> Target:
        target = Target(
            task_id=task_id,
            type=data_type,
            data=data,
        )
        self.session.add(target)
        self.session.commit()
        return target

    def get_by_id(self, target_id) -> Target | None:
        return self.session.query(Target).filter(Target.id == target_id).one_or_none()

    def get_by_task(self, task_id) -> list[Target]:
        return self.session.query(Target).filter(Target.task_id == task_id).all()

    def delete_old_targets(self, task_id):
        targets = self.get_by_task(task_id)
        for target in targets:
            self.session.delete(target)
        self.session.commit()
        return True


def get_target_repository(db: SessionDep) -> TargetRepo:
    return TargetRepo(db)


TargetRepoDep = Annotated[TargetRepo, Depends(get_target_repository)]
