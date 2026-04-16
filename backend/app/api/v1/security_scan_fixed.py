"""Security scan endpoints for OpsPilot."""
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.security_scan import SecurityScan, SecurityScanReport
from app.models.server import Server
from app.models.user import User
from app.core.salt import salt_client
from app.core.config import settings

# Initialize background tasks
from fastapi import BackgroundTasks
background_tasks = BackgroundTasks()

router = APIRouter()


class SecurityScanRequest(BaseModel):
    """Request model for security scan."""
    scan_type: str = Field(..., description="Type of scan: vulnerability, compliance, penetration")
    scan_metadata: Dict[str, Any] = Field(default={}, description="Scan parameters and options")
    server_ids: List[str] = Field(default=[], description="List of server IDs to scan (empty for all)")


class SecurityScanResponse(BaseModel):
    """Response model for security scan."""
    scan_id: str
    status: str
    message: str


class SecurityScanStatusResponse(BaseModel):
    """Response model for security scan status."""
    scan_id: str
    status: str
    progress: float = Field(0, description="Progress percentage (0-100)")
    current_step: str = Field("", description="Current scan step")
    total_steps: int = Field(0, description="Total steps in scan")
    completed_steps: int = Field(0, description="Steps completed")
    estimated_remaining: int = Field(0, description="Estimated seconds remaining")
    started_at: datetime = Field(None, description="Scan start time")
    completed_at: datetime = Field(None, description="Scan completion time")
    scan_duration: int = Field(0, description="Scan duration in seconds")
    total_vulnerabilities: int = Field(0, description="Total vulnerabilities found")
    critical_vulnerabilities: int = Field(0, description="Critical vulnerabilities")
    high_vulnerabilities: int = Field(0, description="High vulnerabilities")
    medium_vulnerabilities: int = Field(0, description="Medium vulnerabilities")
    low_vulnerabilities: int = Field(0, description="Low vulnerabilities")
    info_vulnerabilities: int = Field(0, description="Info vulnerabilities")


@router.post("/security-scans")
async def start_security_scan(
    request: SecurityScanRequest,
    db: AsyncSession = Depends(get_db),
):
    """Start a security scan on servers."""
    
    # Validate scan type
    valid_scan_types = ["vulnerability", "compliance", "penetration"]
    if request.scan_type not in valid_scan_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scan type. Must be one of: {', '.join(valid_scan_types)}",
        )
    
    # Generate unique scan ID
    scan_id = f"scan-{int(time.time())}-{request.scan_type[:4]}-{hash(request.scan_metadata)[:8]}"
    
    # Get servers to scan
    servers_to_scan = []
    if request.server_ids:
        # Scan specific servers
        result = await db.execute(
            select(Server).where(Server.id.in_(request.server_ids))
        )
        servers_to_scan = result.scalars().all()
    else:
        # Scan all servers
        result = await db.execute(select(Server))
        servers_to_scan = result.scalars().all()
    
    if not servers_to_scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No servers found to scan.",
        )
    
    # Create security scan record
    scan = SecurityScan(
        id=scan_id,
        server_id=servers_to_scan[0].id,  # Use first server ID as reference
        scan_type=request.scan_type,
        scan_metadata=request.scan_metadata,
        status="pending",
        results={},
        summary={},
        severity_counts={},
        total_vulnerabilities=0,
        critical_vulnerabilities=0,
        high_vulnerabilities=0,
        medium_vulnerabilities=0,
        low_vulnerabilities=0,
        info_vulnerabilities=0,
        scan_duration=0,
        started_at=None,
        completed_at=None,
    )
    
    db.add(scan)
    await db.commit()
    
    # Start scan in background
    background_tasks.add_task(_run_security_scan, scan, servers_to_scan, db)
    
    return SecurityScanResponse(
        scan_id=scan.id,
        status="started",
        message=f"Security scan {scan_id} started. Check status endpoint for progress."
    )


@router.get("/security-scans/{scan_id}/status")
async def get_security_scan_status(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get security scan status and progress."""
    
    result = await db.execute(
        select(SecurityScan).where(SecurityScan.id == scan_id)
    )
    scan = result.scalar_one_or_none()
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Security scan not found.",
        )
    
    # Calculate progress if running
    progress = 0
    current_step = ""
    total_steps = 0
    completed_steps = 0
    estimated_remaining = 0
    
    if scan.status == "running":
        # Simulate progress calculation (in real implementation, this would be from scan results)
        progress = 65  # Example progress
        current_step = "Analyzing vulnerabilities"
        total_steps = 10
        completed_steps = 6
        estimated_remaining = 120  # seconds
    
    return SecurityScanStatusResponse(
        scan_id=scan.id,
        status=scan.status,
        progress=progress,
        current_step=current_step,
        total_steps=total_steps,
        completed_steps=completed_steps,
        estimated_remaining=estimated_remaining,
        started_at=scan.started_at,
        completed_at=scan.completed_at,
        scan_duration=scan.scan_duration,
        total_vulnerabilities=scan.total_vulnerabilities,
        critical_vulnerabilities=scan.critical_vulnerabilities,
        high_vulnerabilities=scan.high_vulnerabilities,
        medium_vulnerabilities=scan.medium_vulnerabilities,
        low_vulnerabilities=scan.low_vulnerabilities,
        info_vulnerabilities=scan.info_vulnerabilities,
    )


@router.get("/security-scans/{scan_id}/results")
async def get_security_scan_results(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get security scan results."""
    
    result = await db.execute(
        select(SecurityScan).where(SecurityScan.id == scan_id)
    )
    scan = result.scalar_one_or_none()
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Security scan not found.",
        )
    
    if scan.status not in ["completed", "failed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scan results only available for completed or failed scans.",
        )
    
    return {
        "scan_id": scan.id,
        "scan_type": scan.scan_type,
        "status": scan.status,
        "summary": scan.summary,
        "severity_counts": scan.severity_counts,
        "total_vulnerabilities": scan.total_vulnerabilities,
        "results": scan.results,
        "scan_duration": scan.scan_duration,
        "started_at": scan.started_at,
        "completed_at": scan.completed_at,
    }


@router.get("/security-scans/{scan_id}/report")
async def get_security_scan_report(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get security scan report."""
    
    result = await db.execute(
        select(SecurityScan).where(SecurityScan.id == scan_id)
    )
    scan = result.scalar_one_or_none()
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Security scan not found.",
        )
    
    result = await db.execute(
        select(SecurityScanReport).where(SecurityScanReport.scan_id == scan_id)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Security scan report not found.",
        )
    
    return {
        "scan_id": report.scan_id,
        "report_type": report.report_type,
        "report_format": report.report_format,
        "generated_at": report.generated_at,
        "report_content": report.report_content,
    }


@router.post("/security-scans/{scan_id}/cancel")
async def cancel_security_scan(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Cancel a running security scan."""
    
    result = await db.execute(
        select(SecurityScan).where(SecurityScan.id == scan_id)
    )
    scan = result.scalar_one_or_none()
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Security scan not found.",
        )
    
    if scan.status not in ["running", "pending"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scan can only be cancelled if running or pending.",
        )
    
    scan.status = "cancelled"
    scan.completed_at = datetime.utcnow()
    await db.commit()
    
    return {
        "scan_id": scan.id,
        "status": scan.status,
        "message": "Security scan cancelled successfully.",
    }


# Background task functions
import asyncio
import logging

logger = logging.getLogger(__name__)


async def _simulate_scan_step(
    step: str,
    scan: SecurityScan,
    progress: float,
    completed_steps: int,
    total_steps: int,
    db: AsyncSession,
):
    """Simulate a scan step (placeholder for real implementation)."""
    # In real implementation, this would:
    # 1. Use SaltStack to run security scans on servers
    # 2. Parse results
    # 3. Update scan progress
    # 4. Generate findings
    
    # Simulate delay
    await asyncio.sleep(2)  # 2 seconds per step
    
    # Update scan progress
    scan.results["progress"] = {
        "current_step": step,
        "completed_steps": completed_steps,
        "total_steps": total_steps,
        "progress_percentage": progress,
    }
    
    await db.commit()
    
    return True


async def _run_security_scan(scan: SecurityScan, servers: List[Server], db: AsyncSession):
    """Background task to run security scan."""
    try:
        # Update status to running
        scan.status = "running"
        scan.started_at = datetime.utcnow()
        await db.commit()
        
        # Initialize scan results
        scan.results = {
            "scan_type": scan.scan_type,
            "servers_scanned": [server.id for server in servers],
            "scan_metadata": scan.scan_metadata,
            "vulnerabilities": [],
            "findings": [],
            "recommendations": [],
        }
        
        # Simulate scan steps (in real implementation, this would call SaltStack or security tools)
        scan_steps = [
            "Initializing scan tools",
            "Connecting to servers",
            "Scanning for vulnerabilities",
            "Analyzing results",
            "Generating report",
            "Cleanup",
        ]
        
        total_steps = len(scan_steps)
        completed_steps = 0
        
        for step in scan_steps:
            completed_steps += 1
            progress = (completed_steps / total_steps) * 100
            
            await _simulate_scan_step(
                step=step,
                scan=scan,
                progress=progress,
                completed_steps=completed_steps,
                total_steps=total_steps,
                db=db,
            )
            
            # Check if cancelled
            await db.refresh(scan)
            if scan.status == "cancelled":
                logger.info(f"Scan {scan.id} was cancelled")
                return
        
        # Simulate finding vulnerabilities (for demo)
        if scan.scan_type == "vulnerability":
            vulnerabilities = [
                {
                    "id": f"VULN-{int(time.time())}-001",
                    "severity": "high",
                    "title": "Outdated OpenSSL",
                    "description": "OpenSSL version 1.0.1 is vulnerable to Heartbleed",
                    "affected_servers": [server.id for server in servers[:2]],
                    "recommendation": "Update OpenSSL to 1.1.1 or later",
                    "cve": "CVE-2014-0160",
                },
                {
                    "id": f"VULN-{int(time.time())}-002",
                    "severity": "medium",
                    "title": "Weak SSH cipher",
                    "description": "SSH using weak cipher suite",
                    "affected_servers": [server.id for server in servers[2:3] if len(servers) > 2],
                    "recommendation": "Update SSH to use stronger ciphers",
                    "cve": "CVE-2021-3450",
                },
            ]
            
            scan.results["vulnerabilities"] = vulnerabilities
            
            # Update severity counts
            for vuln in vulnerabilities:
                if vuln["severity"] == "critical":
                    scan.critical_vulnerabilities += 1
                elif vuln["severity"] == "high":
                    scan.high_vulnerabilities += 1
                elif vuln["severity"] == "medium":
                    scan.medium_vulnerabilities += 1
                elif vuln["severity"] == "low":
                    scan.low_vulnerabilities += 1
                elif vuln["severity"] == "info":
                    scan.info_vulnerabilities += 1
            
            scan.total_vulnerabilities = (
                scan.critical_vulnerabilities +
                scan.high_vulnerabilities +
                scan.medium_vulnerabilities +
                scan.low_vulnerabilities +
                scan.info_vulnerabilities
            )
        
        # Update final status
        scan.status = "completed"
        scan.completed_at = datetime.utcnow()
        scan.scan_duration = (scan.completed_at - scan.started_at).total_seconds()
        
        # Generate summary
        scan.summary = {
            "scan_type": scan.scan_type,
            "servers_scanned": len(servers),
            "total_vulnerabilities": scan.total_vulnerabilities,
            "severity_distribution": scan.get_severity_distribution(),
            "scan_duration": scan.scan_duration,
            "started_at": scan.started_at,
            "completed_at": scan.completed_at,
        }
        
        # Generate report
        await _generate_security_report(scan, db)
        
        await db.commit()
        
        logger.info(f"Security scan {scan.id} completed successfully")
        
    except Exception as e:
        # Handle errors
        scan.status = "failed"
        scan.completed_at = datetime.utcnow()
        scan.results["error"] = str(e)
        await db.commit()
        raise


async def _generate_security_report(scan: SecurityScan, db: AsyncSession):
    """Generate security scan report."""
    # Generate HTML report content
    report_content = {
        "scan_id": scan.id,
        "scan_type": scan.scan_type,
        "status": scan.status,
        "summary": scan.summary,
        "severity_counts": scan.severity_counts,
        "total_vulnerabilities": scan.total_vulnerabilities,
        "results": scan.results,
        "generated_at": datetime.utcnow().isoformat(),
    }
    
    # Create report record
    report = SecurityScanReport(
        scan_id=scan.id,
        report_type="html",
        report_format="detailed",
        report_content=report_content,
    )
    
    db.add(report)
    await db.commit()