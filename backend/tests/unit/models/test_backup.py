"""Unit tests for backup models (match `app.models.backup`)."""
import uuid

import pytest

from app.models.backup import BackupReport, BackupSchedule


@pytest.mark.unit
def test_backup_schedule_tablename() -> None:
    assert BackupSchedule.__tablename__ == "backup_schedules"


@pytest.mark.unit
def test_backup_report_tablename() -> None:
    assert BackupReport.__tablename__ == "backup_reports"


@pytest.mark.unit
def test_backup_schedule_repr() -> None:
    sid = uuid.uuid4()
    oid = uuid.uuid4()
    sched = BackupSchedule(
        id=uuid.uuid4(),
        server_id=sid,
        organization_id=oid,
        name="nightly",
        schedule_type="daily",
        created_at="2026-01-01",
        updated_at="2026-01-01",
    )
    assert "nightly" in repr(sched)


@pytest.mark.unit
def test_backup_report_repr() -> None:
    rid = uuid.uuid4()
    sid = uuid.uuid4()
    oid = uuid.uuid4()
    report = BackupReport(
        id=rid,
        backup_schedule_id=None,
        server_id=sid,
        organization_id=oid,
        status="completed",
        created_at="2026-01-01",
        updated_at="2026-01-01",
    )
    assert "completed" in repr(report)
