from types import SimpleNamespace

import pytest

from app.core.errors import ForbiddenError
from app.models.enums import Role
from app.models.user import User
from app.services.notification_service import send_status_email
from app.services.report_service import render_report


@pytest.mark.asyncio
async def test_require_admin_rejects_non_admin() -> None:
    from app.core.deps import require_admin

    user = User(
        name="Regular",
        email="regular@example.com",
        password_hash="hash",
        role=Role.USER,
        is_active=True,
    )
    with pytest.raises(ForbiddenError):
        await require_admin(user)


def test_report_json_and_csv_rendering() -> None:
    payload = {
        "generated_at": "2026-09-21T00:00:00+00:00",
        "analytics": {"users": 1, "jobs_by_mode": {"SERVER": 1, "BROWSER": 2}},
        "storage": {"storage_used": 10, "files_count": 2, "stored_files_count": 1},
    }
    json_body, json_type, json_name = render_report(payload, "json")
    csv_body, csv_type, csv_name = render_report(payload, "csv")
    assert '"jobs_by_mode"' in json_body
    assert json_type == "application/json"
    assert json_name.endswith(".json")
    assert "analytics,users,1" in csv_body
    assert csv_type == "text/csv"
    assert csv_name.endswith(".csv")


@pytest.mark.asyncio
async def test_status_email_console_path(monkeypatch) -> None:
    from app.services import notification_service

    events = []
    monkeypatch.setattr(
        notification_service,
        "get_settings",
        lambda: SimpleNamespace(
            smtp_host="",
            smtp_port=587,
            smtp_user="",
            smtp_password="",
            smtp_from="no-reply@example.local",
        ),
    )
    monkeypatch.setattr(notification_service.logger, "info", lambda event, **kwargs: events.append((event, kwargs)))
    await send_status_email("user@example.com", "Demo", "COMPLETED")
    assert events[0][0] == "status_email_console"
