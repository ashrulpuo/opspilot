"""Smoke tests for `EmailService` (no `set_smtp_config`; uses settings-backed fields)."""
import pytest

from app.core.email import EmailService


@pytest.mark.unit
def test_email_service_init_exposes_smtp_fields() -> None:
    svc = EmailService()
    assert hasattr(svc, "smtp_host")
    assert hasattr(svc, "smtp_port")
    assert hasattr(svc, "send_email")


@pytest.mark.unit
def test_send_email_returns_false_when_smtp_not_configured() -> None:
    svc = EmailService()
    if svc.smtp_host:
        pytest.skip("SMTP host is configured; skipping no-op send test")
    ok = svc.send_email(
        to_emails=["nobody@example.com"],
        subject="Test",
        html_content="<p>Hi</p>",
    )
    assert ok is False
