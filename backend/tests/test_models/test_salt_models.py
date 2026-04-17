"""
Unit tests for Salt models.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.models.salt_minion import SaltMinion
from backend.app.models.salt_event import SaltEvent
from backend.app.models.salt_service_state import SaltServiceState
from backend.app.models.salt_process import SaltProcess
from backend.app.models.salt_package import SaltPackage
from backend.app.models.salt_log import SaltLog


class TestSaltMinion:
    """Tests for SaltMinion model."""
    
    def test_create_minion(self, db_session: Session):
        """Test creating a salt minion."""
        minion = SaltMinion(
            minion_id="webserver-01",
            server_id=1,
            grains_info={
                "os_family": "Debian",
                "osfullname": "Debian GNU/Linux",
                "osrelease": "12",
                "kernel": "6.1.0-9-amd64",
                "hostname": "webserver-01",
                "fqdn": "webserver-01.example.com",
                "osarch": "amd64",
                "num_cpus": 4,
                "mem_total": 8589934592,  # 8GB
            },
            last_seen=datetime.now(timezone.utc),
            last_highstate=datetime.now(timezone.utc),
            highstate_success=True
        )
        
        db_session.add(minion)
        db_session.commit()
        
        assert minion.id is not None
        assert minion.minion_id == "webserver-01"
        assert minion.server_id == 1
        assert minion.grains_info["os_family"] == "Debian"
        assert minion.highstate_success is True
    
    def test_minion_relationships(self, db_session: Session):
        """Test minion relationships with other models."""
        minion = SaltMinion(
            minion_id="db-server-01",
            server_id=2,
            grains_info={"os_family": "Ubuntu"},
            last_seen=datetime.now(timezone.utc)
        )
        
        # Create related salt event
        event = SaltEvent(
            server_id=2,
            event_type="highstate",
            event_data={"success": True}
        )
        
        db_session.add(minion)
        db_session.add(event)
        db_session.commit()
        
        assert minion.id is not None
        assert event.server_id == minion.server_id


class TestSaltEvent:
    """Tests for SaltEvent model."""
    
    def test_create_event(self, db_session: Session):
        """Test creating a salt event."""
        event = SaltEvent(
            server_id=1,
            event_type="highstate",
            event_data={
                "success": True,
                "duration": 42.5,
                "changes": {
                    "/etc/nginx/nginx.conf": {
                        "old": "old config",
                        "new": "new config"
                    }
                }
            },
            processed=True
        )
        
        db_session.add(event)
        db_session.commit()
        
        assert event.id is not None
        assert event.server_id == 1
        assert event.event_type == "highstate"
        assert event.event_data["success"] is True
        assert event.processed is True
    
    def test_event_timestamp(self, db_session: Session):
        """Test event has proper timestamp."""
        before = datetime.now(timezone.utc)
        
        event = SaltEvent(
            server_id=1,
            event_type="beacon",
            event_data={"event": "disk_usage", "value": 85}
        )
        
        db_session.add(event)
        db_session.commit()
        
        after = datetime.now(timezone.utc)
        
        assert event.timestamp is not None
        assert before <= event.timestamp <= after


class TestSaltServiceState:
    """Tests for SaltServiceState model."""
    
    def test_create_service_state(self, db_session: Session):
        """Test creating a service state."""
        service = SaltServiceState(
            server_id=1,
            service_name="nginx",
            status="running",
            previous_status="stopped",
            last_checked=datetime.now(timezone.utc)
        )
        
        db_session.add(service)
        db_session.commit()
        
        assert service.id is not None
        assert service.server_id == 1
        assert service.service_name == "nginx"
        assert service.status == "running"
        assert service.previous_status == "stopped"
    
    def test_service_status_transitions(self, db_session: Session):
        """Test tracking service status changes."""
        # Create initial state
        service1 = SaltServiceState(
            server_id=1,
            service_name="postgresql",
            status="running",
            last_checked=datetime.now(timezone.utc)
        )
        
        # Create state change
        service2 = SaltServiceState(
            server_id=1,
            service_name="postgresql",
            status="stopped",
            previous_status="running",
            last_checked=datetime.now(timezone.utc)
        )
        
        db_session.add(service1)
        db_session.add(service2)
        db_session.commit()
        
        # Get latest state for service
        services = db_session.query(SaltServiceState).filter(
            SaltServiceState.service_name == "postgresql"
        ).order_by(SaltServiceState.last_checked.desc()).all()
        
        assert len(services) == 2
        assert services[0].status == "stopped"
        assert services[0].previous_status == "running"


class TestSaltProcess:
    """Tests for SaltProcess model."""
    
    def test_create_process(self, db_session: Session):
        """Test creating a process."""
        process = SaltProcess(
            server_id=1,
            pid=1234,
            name="nginx",
            command="nginx: master process /etc/nginx/nginx.conf",
            username="www-data",
            cpu_percent=2.5,
            memory_percent=1.2,
            state="S",
            start_time=datetime.now(timezone.utc)
        )
        
        db_session.add(process)
        db_session.commit()
        
        assert process.id is not None
        assert process.pid == 1234
        assert process.name == "nginx"
        assert process.cpu_percent == 2.5
        assert process.memory_percent == 1.2
        assert process.state == "S"


class TestSaltPackage:
    """Tests for SaltPackage model."""
    
    def test_create_package(self, db_session: Session):
        """Test creating a package."""
        package = SaltPackage(
            server_id=1,
            name="nginx",
            version="1.24.0-2",
            architecture="amd64",
            source="dpkg",
            is_update_available=True,
            installed_date=datetime.now(timezone.utc),
            update_version="1.25.0-1"
        )
        
        db_session.add(package)
        db_session.commit()
        
        assert package.id is not None
        assert package.name == "nginx"
        assert package.version == "1.24.0-2"
        assert package.is_update_available is True
        assert package.update_version == "1.25.0-1"
    
    def test_package_without_update(self, db_session: Session):
        """Test package without available update."""
        package = SaltPackage(
            server_id=1,
            name="python3",
            version="3.11.2-1",
            architecture="amd64",
            source="dpkg",
            is_update_available=False,
            installed_date=datetime.now(timezone.utc)
        )
        
        db_session.add(package)
        db_session.commit()
        
        assert package.id is not None
        assert package.is_update_available is False
        assert package.update_version is None


class TestSaltLog:
    """Tests for SaltLog model."""
    
    def test_create_log(self, db_session: Session):
        """Test creating a log entry."""
        log = SaltLog(
            server_id=1,
            timestamp=datetime.now(timezone.utc),
            log_level="INFO",
            source="nginx",
            message="Configuration reloaded successfully",
            metadata={
                "config_file": "/etc/nginx/nginx.conf",
                "pid": 1234
            }
        )
        
        db_session.add(log)
        db_session.commit()
        
        assert log.id is not None
        assert log.server_id == 1
        assert log.log_level == "INFO"
        assert log.source == "nginx"
        assert log.message == "Configuration reloaded successfully"
        assert log.metadata["config_file"] == "/etc/nginx/nginx.conf"
    
    def test_log_error_level(self, db_session: Session):
        """Test error log entry."""
        log = SaltLog(
            server_id=1,
            timestamp=datetime.now(timezone.utc),
            log_level="ERROR",
            source="postgresql",
            message="Connection failed: connection refused"
        )
        
        db_session.add(log)
        db_session.commit()
        
        assert log.log_level == "ERROR"
        assert log.message.startswith("Connection failed")
