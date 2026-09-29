import smtplib
from email.message import EmailMessage

from app.core.config import get_settings
from app.core.logging import logger


async def send_password_reset_email(email: str, reset_token: str) -> None:
    settings = get_settings()
    subject = "Reset your subtitle platform password"
    body = f"Use this password reset token: {reset_token}"
    if not settings.smtp_host:
        logger.info("password_reset_email_console", email=email, reset_token=reset_token)
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from
    message["To"] = email
    message.set_content(body)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        smtp.starttls()
        if settings.smtp_user:
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(message)


async def send_status_email(email: str, project_title: str, status: str) -> None:
    settings = get_settings()
    subject = f"Subtitle project {status.lower()}"
    body = f"Your project '{project_title}' is now {status}."
    if not settings.smtp_host:
        logger.info("status_email_console", email=email, project_title=project_title, status=status)
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from
    message["To"] = email
    message.set_content(body)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        smtp.starttls()
        if settings.smtp_user:
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(message)
