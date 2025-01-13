import enum


class RoleJob(enum.Enum):
    WRITE_TASK = "write_task"
    EDITOR = "editor"
    MAIN_EDITOR = "main_editor"
    ANALYST = "analyst"
    MARKETING = "marketing"
    APPROVE = "approve"


class RoleJobState(enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    DONE = "done"


ROLE_JOB_OPENS = {
    RoleJob.WRITE_TASK: [RoleJob.EDITOR, RoleJob.ANALYST],
    RoleJob.EDITOR: [RoleJob.MAIN_EDITOR],
    RoleJob.ANALYST: [RoleJob.MARKETING],
    RoleJob.MAIN_EDITOR: [RoleJob.APPROVE],
    RoleJob.MARKETING: [RoleJob.APPROVE],
    RoleJob.APPROVE: [],
}

ROLE_JOB_OPENED_BY = {
    RoleJob.WRITE_TASK: [],
    RoleJob.EDITOR: [RoleJob.WRITE_TASK],
    RoleJob.MAIN_EDITOR: [RoleJob.EDITOR],
    RoleJob.ANALYST: [RoleJob.WRITE_TASK],
    RoleJob.MARKETING: [RoleJob.ANALYST],
    RoleJob.APPROVE: [RoleJob.MAIN_EDITOR, RoleJob.MARKETING],
}


def default_checks_dict() -> dict[str, str]:
    result = {job.value: RoleJobState.NOT_STARTED.value for job in RoleJob}
    result[RoleJob.WRITE_TASK.value] = RoleJobState.IN_PROGRESS.value
    return result
