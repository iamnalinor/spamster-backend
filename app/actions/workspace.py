from app.deps.email_sender import (
    AbstractSender,
    EmailSender,
    Message,
    SMTPConfig,
    create_default_email_config,
)
from app.repo.workspace import WorkspaceRepo


def notify_roles_in_workspace(
    workspace_repo: WorkspaceRepo,
    workspace_id: int,
    roles: list[str],
    message: Message,
    *,
    sender: AbstractSender | None = None,
):
    if not sender:
        sender = EmailSender(get_workspace_email_config(workspace_repo, workspace_id))

    members = [
        member.user.email
        for member in workspace_repo.get_members(workspace_id)
        if member.role.value in roles
    ]
    print(f"Mass sending {message.text} for {members}")
    mass_send(
        members,
        sender,
        message,
    )


def get_workspace_email_config(
    workspace_repo: WorkspaceRepo, workspace_id: int
) -> SMTPConfig:
    ws = workspace_repo.find_by_id(workspace_id)
    if not ws.smtp_email:
        return create_default_email_config()
    return SMTPConfig(
        host=ws.smtp_host,
        port=ws.smtp_port,
        email=ws.smtp_email,
        password=ws.smtp_password,
    )


def mass_send(addresses: list[str], sender: AbstractSender, message: Message):
    for address in addresses:
        sender.send(address, message)
