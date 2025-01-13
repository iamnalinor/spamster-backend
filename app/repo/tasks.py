from typing import Annotated

from fastapi import Depends
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.deps.database import SessionDep
from app.enums.rolejobs import default_checks_dict
from app.models import Task, TaskComment, TaskUpdateEvent


class TasksRepo:
    def __init__(self, session: Session):
        self.session = session

    def get_task(self, task_id: int):
        """Get a task by ID"""
        return self.session.query(Task).filter(Task.id == task_id).first()

    def get_workspace_tasks(self, workspace_id: int):
        """Get all tasks for a workspace and user"""
        return self.session.query(Task).filter(Task.workspace_id == workspace_id).all()

    def create_task(
        self,
        workspace_id: int,
        user_id: int,
        name: str,
        description: str,
        subject: str = "",
        content: str = "",
    ):
        """Create a new task"""
        task = Task(
            workspace_id=workspace_id,
            author_id=user_id,
            name=name,
            description=description,
            subject=subject,
            content=content,
            checks=default_checks_dict(),
            files=[],
        )
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        task_event = TaskUpdateEvent(
            task_id=task.id,
            author_id=user_id,
            prev={
                "name": "",
                "description": "",
                "subject": "",
                "content": "",
            },
            data={
                "name": name,
                "description": description,
                "subject": subject,
                "content": content,
            },
        )
        self.session.add(task_event)
        self.session.commit()
        return task

    def update_task(self, task_id: int, user_id: int, **updates):
        """Update a task with the given fields"""
        task = self.get_task(task_id)
        prev = {field: getattr(task, field) for field in updates}
        if task:
            for field, value in updates.items():
                setattr(task, field, value)
            task_event = TaskUpdateEvent(
                task_id=task.id, author_id=user_id, prev=prev, data=updates
            )
            self.session.add(task)
            self.session.add(task_event)
            self.session.commit()
        return task

    def delete_task(self, task_id: int) -> bool:
        """Delete a task"""
        task = self.get_task(task_id)
        if task:
            self.session.delete(task)
            self.session.commit()
            return True
        return False

    def create_comment(self, task_id: int, user_id: int, text: str) -> TaskComment:
        """Create a new comment on a task"""
        comment = TaskComment(task_id=task_id, user_id=user_id, text=text)
        self.session.add(comment)
        self.session.commit()
        self.session.refresh(comment)
        return comment

    def get_task_comments(self, task_id: int) -> list[TaskComment]:
        """Get all comments for a task"""
        return (
            self.session.query(TaskComment).filter(TaskComment.task_id == task_id).all()
        )

    def get_task_history(self, task_id: int) -> list[TaskUpdateEvent]:
        """Get all events for a task"""
        return (
            self.session.query(TaskUpdateEvent)
            .filter(TaskUpdateEvent.task_id == task_id)
            .all()
        )

    def get_by_id(self, tid: int) -> Task | None:
        return self.session.query(Task).filter(Task.id == tid).one_or_none()

    def set_files(self, task_id: int, files: list[str]) -> None:
        stmt = update(Task).where(Task.id == task_id).values(files=files)
        self.session.execute(stmt)
        self.session.commit()

    def archive_task(self, task_id: int) -> Task:
        task = self.get_by_id(task_id)
        task.is_archived = True
        self.session.add(task)
        self.session.commit()
        return task


def get_tasks_repository(db: SessionDep) -> TasksRepo:
    return TasksRepo(db)


TasksRepoDep = Annotated[TasksRepo, Depends(get_tasks_repository)]
