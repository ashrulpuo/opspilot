"""Security scan model for OpsPilot."""
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy import Column, String, Integer, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class SecurityScan(Base):
    """Security scan model for storing scan results."""
    
    __tablename__ = "security_scans"
    
    id = Column(String, primary_key=True)
    server_id = Column(String, ForeignKey("servers.id"), nullable=False, index=True)
    scan_type = Column(String, nullable=False, index=True)  # e.g., "vulnerability", "compliance", "penetration"
    status = Column(String, nullable=False, default="pending", index=True)  # pending, running, completed, failed, cancelled
    scan_metadata = Column(JSON, default={})  # scan parameters, options, etc.
    results = Column(JSON, default={})  # scan results, vulnerabilities, etc.
    summary = Column(JSON, default={})  # summary statistics
    severity_counts = Column(JSON, default={})  # critical, high, medium, low, info
    total_vulnerabilities = Column(Integer, default=0)
    critical_vulnerabilities = Column(Integer, default=0)
    high_vulnerabilities = Column(Integer, default=0)
    medium_vulnerabilities = Column(Integer, default=0)
    low_vulnerabilities = Column(Integer, default=0)
    info_vulnerabilities = Column(Integer, default=0)
    scan_duration = Column(Integer, default=0)  # seconds
    started_at = Column(DateTime, nullable=True, index=True)
    completed_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    server = relationship("Server", foreign_keys=[server_id])
    
    def is_complete(self) -> bool:
        """Check if scan is complete (completed or failed)."""
        return self.status in ["completed", "failed", "cancelled"]
    
    def get_severity_distribution(self) -> Dict[str, int]:
        """Get vulnerability severity distribution."""
        return {
            "critical": self.critical_vulnerabilities,
            "high": self.high_vulnerabilities,
            "medium": self.medium_vulnerabilities,
            "low": self.low_vulnerabilities,
            "info": self.info_vulnerabilities
        }
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics."""
        return {
            "total_vulnerabilities": self.total_vulnerabilities,
            "severity_counts": self.get_severity_distribution(),
            "scan_duration": self.scan_duration,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at
        }
    
    def __repr__(self) -> str:
        return f"<SecurityScan(id={self.id}, server_id={self.server_id}, scan_type={self.scan_type}, status={self.status})>"


class SecurityScanReport(Base):
    """Security scan report model for generating reports."""
    
    __tablename__ = "security_scan_reports"
    
    id = Column(String, primary_key=True)
    scan_id = Column(String, ForeignKey("security_scans.id"), nullable=False, index=True)
    report_type = Column(String, nullable=False, default="html")  # html, pdf, json
    report_format = Column(String, nullable=False, default="detailed")  # detailed, summary, executive
    report_content = Column(JSON, default={})  # report data
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    scan = relationship("SecurityScan", back_populates="reports")
    
    def __repr__(self) -> str:
        return f"<SecurityScanReport(id={self.id}, scan_id={self.scan_id}, report_type={self.report_type})>"


# Add relationship to SecurityScan
SecurityScan.reports = relationship("SecurityScanReport", order_by=SecurityScanReport.generated_at, back_populates="scan")