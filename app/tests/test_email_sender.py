import pytest

from app import config
from app.actions.workspace import mass_send, notify_roles_in_workspace
from app.deps.email_sender import (
    Attachment,
    Message,
    MockTestSender,
    SMTPConfig,
    create_default_sender,
)


def test_test_sender_stores_messages():
    sender = MockTestSender()
    message = Message("Test", "Test message")

    sender.send("test@example.com", message)

    assert len(sender.sent_messages) == 1
    assert sender.sent_messages[0] == ("test@example.com", message)


def test_test_sender_clear():
    sender = MockTestSender()
    message = Message("Test", "Test message")
    sender.send("test@example.com", message)

    sender.clear()

    assert len(sender.sent_messages) == 0


def test_message_with_attachments():
    message = Message(
        "Test with attachment",
        "Test message",
        attachments=[Attachment("test.txt", b"test content")],
    )

    assert len(message.attachments) == 1
    assert message.attachments[0].filename == "test.txt"
    assert message.attachments[0].content == b"test content"


def test_message_default_no_attachments():
    message = Message("Test", "Test message")

    assert message.attachments == []


def test_smtp_config():
    config = SMTPConfig(
        host="smtp.example.com",
        port=587,
        email="test@example.com",
        password="password123",
    )

    assert config.host == "smtp.example.com"
    assert config.port == 587
    assert config.email == "test@example.com"
    assert config.password == "password123"


def test_mass_send():
    sender = MockTestSender()
    message = Message("Test", "Test message")
    addresses = ["test1@example.com", "test2@example.com", "test3@example.com"]

    mass_send(addresses, sender, message)

    assert len(sender.sent_messages) == 3
    assert sender.sent_messages[0] == ("test1@example.com", message)
    assert sender.sent_messages[1] == ("test2@example.com", message)
    assert sender.sent_messages[2] == ("test3@example.com", message)


def test_notify_roles_in_workspace(mocker):
    workspace_repo = mocker.Mock()
    email_sender = MockTestSender()
    workspace_id = 1
    roles = ["admin", "member"]
    message = Message("Test", "Test message")

    workspace_repo.get_members.return_value = [
        mocker.Mock(
            user=mocker.Mock(email="user1@example.com"), role=mocker.Mock(value="admin")
        ),
        mocker.Mock(
            user=mocker.Mock(email="user2@example.com"),
            role=mocker.Mock(value="member"),
        ),
        mocker.Mock(
            user=mocker.Mock(email="user3@example.com"), role=mocker.Mock(value="guest")
        ),
    ]

    notify_roles_in_workspace(
        workspace_repo,
        workspace_id,
        roles,
        message,
        sender=email_sender,
    )

    workspace_repo.get_members.assert_called_once_with(workspace_id)
    assert len(email_sender.sent_messages) == 2


@pytest.mark.skipif(not config.SMTP_CONFIG_EMAIL, reason="SMTP is not configured")
def test_real_send():
    sender = create_default_sender()

    # let's flood my secondary email
    sender.send(
        "example@gmail.com",
        Message(
            "The answer",
            "Look at that funny cat!",
            attachments=[Attachment("42.txt", b" 4 2 ")],
        ),
    )
    message = Message(
        "Test email",
        "This is a test message. Sent by FastAPI with testing purposes. "
        "Absolutely not a spam on real gmail address.",
    )
    sender.send("example@gmail.com", message)
