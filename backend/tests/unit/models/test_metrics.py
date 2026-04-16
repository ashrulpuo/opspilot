"""Smoke tests for metrics time-series model."""
import uuid
from datetime import datetime

import pytest

from app.models.metrics import Metric


@pytest.mark.unit
def test_metric_tablename() -> None:
    assert Metric.__tablename__ == "metrics"


@pytest.mark.unit
def test_metric_construct() -> None:
    m = Metric(
        id=str(uuid.uuid4()),
        server_id=str(uuid.uuid4()),
        timestamp=datetime.utcnow(),
        metric_name="cpu_percent",
        metric_value=12.5,
        unit="%",
    )
    assert m.metric_name == "cpu_percent"
    assert m.metric_value == 12.5
