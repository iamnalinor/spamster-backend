import email.encoders
import smtplib
import ssl
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app import config


@dataclass
class SMTPConfig:
    host: str
    port: int
    email: str
    password: str


@dataclass
class Attachment:
    filename: str
    content: bytes


@dataclass
class Message:
    title: str
    text: str
    attachments: list[Attachment] = field(default_factory=list)


class AbstractSender(ABC):
    @abstractmethod
    def send(self, address: str, message: Message):
        raise NotImplementedError


class EmailSender(AbstractSender):
    def __init__(self, smtp_params: SMTPConfig):
        self.smtp_params = smtp_params

    def _compose_attachment(self, attachment: Attachment) -> MIMEBase:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.content)
        email.encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition", f"attachment; filename={attachment.filename}"
        )
        return part

    def _compose_message(self, target_email: str, message_data: Message):
        message = MIMEMultipart()
        message["From"] = self.smtp_params.email
        message["To"] = target_email
        message["Subject"] = message_data.title
        message["Bcc"] = target_email
        message.attach(MIMEText(message_data.text, "plain"))
        for attachment in message_data.attachments:
            message.attach(self._compose_attachment(attachment))
        return message

    def _create_connection(self):
        context = ssl.create_default_context()
        return smtplib.SMTP_SSL(
            self.smtp_params.host, self.smtp_params.port, context=context
        )

    def send(self, target_email: str, message_data: Message):
        message = self._compose_message(target_email, message_data)
        with self._create_connection() as server:
            server.login(self.smtp_params.email, self.smtp_params.password)
            server.sendmail(self.smtp_params.email, target_email, message.as_string())


class MockTestSender(AbstractSender):
    def __init__(self):
        self.sent_messages: list[tuple[str, Message]] = []

    def send(self, address: str, message: Message):
        self.sent_messages.append((address, message))

    def get_sent_messages(self) -> list[tuple[str, Message]]:
        return self.sent_messages

    def clear(self):
        self.sent_messages = []


def create_default_sender() -> EmailSender:
    return EmailSender(create_default_email_config())


def create_default_email_config() -> SMTPConfig:
    if not config.SMTP_CONFIG_EMAIL:
        raise ValueError("SMTP parameters are not configured")
    return SMTPConfig(
        config.SMTP_CONFIG_HOST,
        config.SMTP_CONFIG_PORT,
        config.SMTP_CONFIG_EMAIL,
        config.SMTP_CONFIG_PASSWORD,
    )
