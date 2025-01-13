from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from app.enums.roles import Role


class StageState(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    DONE = "done"


StateChangeObserver = Callable[["WorkflowStage", StageState, StageState], None]


class DependenciesNotDoneError(Exception):
    pass


class StageNotFoundError(Exception):
    pass


class StagePermissionError(Exception):
    pass


class WorkflowStage:
    def __init__(
        self,
        uid: str,
        name: str,
        depends_on: list["WorkflowStage"],
        roles_for_stage: list[Role],
        state: StageState,
    ):
        self.uid = uid
        self.name = name
        self.depends_on = depends_on
        self._state = state
        self.opens_stages = []
        self.roles_for_stage = roles_for_stage
        for stage in depends_on:
            stage.opens_stages.append(stage)

    def are_dependencies_done(self):
        return all(dep.state == StageState.DONE for dep in self.depends_on)

    @property
    def state(self):
        return self._state

    def mark_as(
        self,
        state: StageState,
        state_change_observer: StateChangeObserver = lambda a, b, c: (),
    ):
        if state != StageState.NOT_STARTED and not self.are_dependencies_done():
            raise DependenciesNotDoneError
        self._state = state
        if state == StageState.DONE:
            for stage in self.opens_stages:
                if stage.are_dependencies_done():
                    state_change_observer(stage, stage.state, StageState.IN_PROGRESS)
                    stage.mark_as(
                        StageState.IN_PROGRESS,
                        state_change_observer=state_change_observer,
                    )


@dataclass
class StageTemplate:
    uid: str
    name: str
    depends_on: list[str]
    roles: list[Role]
    default_state: StageState = StageState.NOT_STARTED


Checklist = dict[str, StageState]


class StagedModel:
    def __init__(self):
        self._stages: dict[str, WorkflowStage] = {}
        self._templated_deps = {}

    def create_stage(self, template: StageTemplate):
        stage = WorkflowStage(
            template.uid, template.name, [], template.roles, template.default_state
        )
        self._stages[template.uid] = stage
        self._templated_deps[template.uid] = template.depends_on

    def link_dependencies(self):
        for uid, stage in self._stages.items():
            if uid not in self._templated_deps:
                continue
            stage.depends_on = [
                self._stages[dep_uid] for dep_uid in self._templated_deps[stage.uid]
            ]
            for dep in stage.depends_on:
                dep.opens_stages.append(stage)
        self._templated_deps.clear()

    def change_state(
        self,
        uid: str,
        state: StageState,
        as_role: Role | None = None,
        state_change_observer: StateChangeObserver = lambda a, b, c: (),
    ):
        if uid not in self._stages:
            raise StageNotFoundError
        stage = self._stages[uid]
        if as_role is not None and as_role not in stage.roles_for_stage:
            raise StagePermissionError
        stage.mark_as(state, state_change_observer)

    def serialize_to_checklist(self) -> Checklist:
        return {uid: stage.state for uid, stage in self._stages.items()}

    def get_stage(self, uid: str) -> WorkflowStage:
        if uid not in self._stages:
            raise StageNotFoundError
        return self._stages[uid]

    def _set_state(self, uid, state):
        self._stages[uid]._state = state

    @staticmethod
    def deserialize_from_checklist(
        checklist: Checklist, templates: list[StageTemplate]
    ) -> "StagedModel":
        model = StagedModel()
        for template in templates:
            model.create_stage(template)
        model.link_dependencies()
        for uid, state in checklist.items():
            if isinstance(state, str):
                state = StageState(state)
            model._set_state(uid, state)
        return model


def mark_as_done(model, role: Role, check_id: str, observer: StateChangeObserver):
    model.change_state(check_id, StageState.DONE, Role(role), observer)


def reject(
    model, role: Role, check_id: str, due_to: list[str], observer: StateChangeObserver
):
    for reason in due_to:
        model.change_state(
            reason, StageState.IN_PROGRESS, state_change_observer=observer
        )
        observer(model.get_stage(reason), StageState.DONE, StageState.IN_PROGRESS)
    model.change_state(check_id, StageState.NOT_STARTED)


TEMPLATES = [
    StageTemplate(
        "write_task",
        "Постановка задачи",
        [],
        [Role.PRODUCT],
        default_state=StageState.IN_PROGRESS,
    ),
    StageTemplate("editor", "Написание текста", ["write_task"], [Role.EDITOR]),
    StageTemplate("analyst", "Подбор ЦА", ["write_task"], [Role.ANALYST]),
    StageTemplate("main_editor", "Проверка главредом", ["editor"], [Role.MAIN_EDITOR]),
    StageTemplate("marketing", "Маркетинг", ["analyst"], [Role.MARKETING]),
    StageTemplate(
        "approve", "Утверждение", ["marketing", "main_editor"], [Role.PRODUCT]
    ),
]


def get_reject_reasons(model: StagedModel, stage_id):
    return [
        {"id": stage.uid, "name": stage.name}
        for stage in model.get_stage(stage_id).depends_on
    ]
