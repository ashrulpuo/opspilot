"""Unit tests for Metrics model."""
import pytest
from datetime import datetime, timedelta
from app.models.metrics import Metric
from app.models.server import Server


@pytest.mark.unit
class TestMetricsModel:
    """Test Metrics model functionality."""

    def test_metric_creation(self):
        """Test metric creation with valid data."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        
        metric = Metric(
            name="cpu_usage",
            value=75.5,
            unit="%",
            server=server
        )
        
        assert metric.name == "cpu_usage"
        assert metric.value == 75.5
        assert metric.unit == "%"
        assert metric.server == server
        assert metric.created_at is not None

    def test_metric_str_representation(self):
        """Test string representation of Metric model."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        
        metric = Metric(
            name="cpu_usage",
            value=75.5,
            unit="%",
            server=server
        )
        
        assert str(metric) == "Metric(name='cpu_usage', value=75.5, unit='%')"

    def test_metric_equality(self):
        """Test metric equality comparison."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        
        metric1 = Metric(
            name="cpu_usage",
            value=75.5,
            unit="%",
            server=server
        )
        
        metric2 = Metric(
            name="cpu_usage",
            value=75.5,
            unit="%",
            server=server
        )
        
        assert metric1 == metric2

    def test_metric_inequality(self):
        """Test metric inequality comparison."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        
        metric1 = Metric(
            name="cpu_usage",
            value=75.5,
            unit="%",
            server=server
        )
        
        metric2 = Metric(
            name="memory_usage",
            value=60.2,
            unit="%",
            server=server
        )
        
        assert metric1 != metric2

    def test_metric_default_values(self):
        """Test default values for Metric model."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        
        metric = Metric(
            name="cpu_usage",
            value=75.5,
            unit="%",
            server=server
        )
        
        assert metric.created_at is not None

    def test_metric_with_server(self):
        """Test metric with server relationship."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        
        metric = Metric(
            name="cpu_usage",
            value=75.5,
            unit="%",
            server=server
        )
        
        assert metric.server == server
        assert metric.server_id == server.id

    def test_metric_creation_without_optional_fields(self):
        """Test metric creation without optional fields."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        
        metric = Metric(
            name="cpu_usage",
            value=75.5,
            server=server
        )
        
        assert metric.name == "cpu_usage"
        assert metric.value == 75.5
        assert metric.unit is None
        assert metric.server == server
        assert metric.created_at is not None

    def test_metric_unit_field(self):
        """Test metric unit field."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        
        metric = Metric(
            name="cpu_usage",
            value=75.5,
            unit="%",
            server=server
        )
        
        assert metric.unit == "%"