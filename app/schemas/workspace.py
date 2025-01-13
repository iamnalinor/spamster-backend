from app.enums import roles
from app.schemas import BaseSchema
from app.schemas.user import UserModel


class WorkspaceBaseModel(BaseSchema):
    name: str


class WorkspaceCreateModel(WorkspaceBaseModel):
    my_role: roles.Role


class WorkspaceUpdateModel(WorkspaceBaseModel):
    pass


class WorkspaceResponseModel(WorkspaceBaseModel):
    id: int
    owner_id: int


class WorkspaceGrantAccessModel(BaseSchema):
    login: str
    role: roles.Role


class WorkspaceRevokeAccessModel(BaseSchema):
    login: str


class WorkspaceMemberModel(BaseSchema):
    user: UserModel
    role: roles.Role
    is_owner: bool
