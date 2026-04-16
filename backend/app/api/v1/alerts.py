"""Alert management API endpoints for OpsPilot."""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.email import email_service
from app.models.alert import Alert
from app.models.server import Server
from app.models.organization import Organization, OrganizationMember

router = APIRouter()


# ============================================
# Request Schemas
# ============================================

class CreateAlertRequest(BaseModel):
    """Manual alert creation request schema."""

    server_id: str
    type: str
    severity: str
    title: str
    message: str
    threshold: Optional[float] = None


class UpdateAlertRequest(BaseModel):
    """Alert update request schema."""

    title: Optional[str] = None
    message: Optional[str] = None
    severity: Optional[str] = None


# ============================================
# Response Schemas
# ============================================

class AlertResponse(BaseModel):
    """Alert response schema."""

    id: str
    server_id: str
    server_hostname: Optional[str]
    organization_id: str
    type: str
    severity: str
    title: str
    message: str
    value: Optional[float]
    threshold: Optional[float]
    resolved: bool
    resolved_at: Optional[str]
    created_at: str
    updated_at: str


class AlertsListResponse(BaseModel):
    """Alerts list response schema."""

    total: int
    page: int
    page_size: int
    total_pages: int
    alerts: List[AlertResponse]


class AlertStatsResponse(BaseModel):
    """Alert statistics response schema."""

    total: int
    active: int
    resolved: int
    critical: int
    warning: int
    info: int


# ============================================
# Endpoints
# ============================================

@router.get("/alerts", response_model=AlertsListResponse)
async def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    server_id: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    resolved: Optional[bool] = Query(None),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """List all alerts for user's organizations.

    Args:
        page: Page number
        page_size: Items per page
        server_id: Filter by server
        severity: Filter by severity
        resolved: Filter by resolved status
        start: Start date filter (ISO format)
        end: End date filter (ISO format)
        db: Database session
        current_user: Current authenticated user

    Returns:
        Paginated list of alerts
    """
    user_id = current_user["id"]

    # Get user's organizations
    org_result = await db.execute(
        select(OrganizationMember.organization_id).where(
            OrganizationMember.user_id == user_id
        )
    )
    org_ids = [row[0] for row in org_result.fetchall()]

    if not org_ids:
        return AlertsListResponse(
            total=0,
            page=page,
            page_size=page_size,
            total_pages=0,
            alerts=[],
        )

    # Build query
    query = (
        select(Alert, Server.hostname)
        .join(Server, Alert.server_id == Server.id)
        .where(Alert.organization_id.in_(org_ids))
    )

    # Apply filters
    if server_id:
        query = query.where(Alert.server_id == server_id)
    if severity:
        query = query.where(Alert.severity == severity)
    if resolved is not None:
        query = query.where(Alert.resolved == resolved)
    if start:
        from datetime import datetime
        start_date = datetime.fromisoformat(start)
        query = query.where(Alert.created_at >= start_date)
    if end:
        from datetime import datetime
        end_date = datetime.fromisoformat(end)
        query = query.where(Alert.created_at <= end_date)

    # Order by created_at desc
    query = query.order_by(Alert.created_at.desc())

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Execute query
    results = await db.execute(query)
    alerts_with_hostnames = results.fetchall()

    # Build response
    alerts = []
    for alert, hostname in alerts_with_hostnames:
        alerts.append(
            AlertResponse(
                id=alert.id,
                server_id=alert.server_id,
                server_hostname=hostname,
                organization_id=alert.organization_id,
                type=alert.type,
                severity=alert.severity,
                title=alert.title,
                message=alert.message,
                value=alert.value,
                threshold=alert.threshold,
                resolved=alert.resolved,
                resolved_at=alert.resolved_at.isoformat() if alert.resolved_at else None,
                created_at=alert.created_at.isoformat(),
                updated_at=alert.updated_at.isoformat(),
            )
        )

    total_pages = (total + page_size - 1) // page_size

    return AlertsListResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        alerts=alerts,
    )


@router.get("/alerts/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get a single alert by ID.

    Args:
        alert_id: Alert ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Alert details

    Raises:
        HTTPException: If alert not found or no permission
    """
    user_id = current_user["id"]

    # Get user's organizations
    org_result = await db.execute(
        select(OrganizationMember.organization_id).where(
            OrganizationMember.user_id == user_id
        )
    )
    org_ids = [row[0] for row in org_result.fetchall()]

    # Get alert
    query = (
        select(Alert, Server.hostname)
        .join(Server, Alert.server_id == Server.id)
        .where(
            Alert.id == alert_id,
            Alert.organization_id.in_(org_ids) if org_ids else False
        )
    )
    result = await db.execute(query)
    alert_data = result.fetchone()

    if not alert_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    alert, hostname = alert_data

    return AlertResponse(
        id=alert.id,
        server_id=alert.server_id,
        server_hostname=hostname,
        organization_id=alert.organization_id,
        type=alert.type,
        severity=alert.severity,
        title=alert.title,
        message=alert.message,
        value=alert.value,
        threshold=alert.threshold,
        resolved=alert.resolved,
        resolved_at=alert.resolved_at.isoformat() if alert.resolved_at else None,
        created_at=alert.created_at.isoformat(),
        updated_at=alert.updated_at.isoformat(),
    )


@router.post("/alerts", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    request: CreateAlertRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Create a new alert manually.

    Args:
        request: Alert creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created alert

    Raises:
        HTTPException: If server not found or no permission
    """
    user_id = current_user["id"]

    # Verify server exists and user has access
    server_result = await db.execute(
        select(Server, OrganizationMember.organization_id)
        .join(OrganizationMember, Server.organization_id == OrganizationMember.organization_id)
        .where(
            Server.id == request.server_id,
            OrganizationMember.user_id == user_id
        )
    )
    server_data = server_result.fetchone()

    if not server_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found or no permission",
        )

    server, org_id = server_data

    # Create alert
    import uuid
    alert = Alert(
        id=str(uuid.uuid4()),
        server_id=server.id,
        organization_id=org_id,
        type=request.type,
        severity=request.severity,
        title=request.title,
        message=request.message,
        threshold=request.threshold,
        resolved=False,
    )

    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    # Send email notification for critical alerts
    if request.severity in ["critical", "warning"]:
        # Get organization members for notification
        org_members_result = await db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.role.in_(["admin", "devops"])
            )
        )
        org_members = org_members_result.fetchall()

        # Collect email addresses
        # TODO: Add email field to User model and get from there
        # For now, this is a placeholder
        to_emails = []  # Will be populated from User.email when available

        # Send email notification
        if to_emails:
            email_service.send_alert_notification(
                to_emails=to_emails,
                alert_data={
                    "id": alert.id,
                    "server_hostname": server.hostname,
                    "type": request.type,
                    "severity": request.severity,
                    "message": request.message,
                    "threshold": request.threshold,
                    "actual_value": alert.value,
                    "triggered_at": alert.created_at.isoformat(),
                }
            )

    return AlertResponse(
        id=alert.id,
        server_id=alert.server_id,
        server_hostname=server.hostname,
        organization_id=alert.organization_id,
        type=alert.type,
        severity=alert.severity,
        title=alert.title,
        message=alert.message,
        value=alert.value,
        threshold=alert.threshold,
        resolved=alert.resolved,
        resolved_at=alert.resolved_at.isoformat() if alert.resolved_at else None,
        created_at=alert.created_at.isoformat(),
        updated_at=alert.updated_at.isoformat(),
    )


@router.put("/alerts/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: str,
    request: UpdateAlertRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Update an alert.

    Args:
        alert_id: Alert ID
        request: Alert update data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated alert

    Raises:
        HTTPException: If alert not found or no permission
    """
    user_id = current_user["id"]

    # Get user's organizations
    org_result = await db.execute(
        select(OrganizationMember.organization_id).where(
            OrganizationMember.user_id == user_id
        )
    )
    org_ids = [row[0] for row in org_result.fetchall()]

    # Get alert
    result = await db.execute(
        select(Alert).where(
            Alert.id == alert_id,
            Alert.organization_id.in_(org_ids) if org_ids else False
        )
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    # Update alert
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(alert, key, value)

    await db.commit()
    await db.refresh(alert)

    # Get server hostname
    server_result = await db.execute(
        select(Server.hostname).where(Server.id == alert.server_id)
    )
    hostname = server_result.scalar_one_or_none()

    return AlertResponse(
        id=alert.id,
        server_id=alert.server_id,
        server_hostname=hostname,
        organization_id=alert.organization_id,
        type=alert.type,
        severity=alert.severity,
        title=alert.title,
        message=alert.message,
        value=alert.value,
        threshold=alert.threshold,
        resolved=alert.resolved,
        resolved_at=alert.resolved_at.isoformat() if alert.resolved_at else None,
        created_at=alert.created_at.isoformat(),
        updated_at=alert.updated_at.isoformat(),
    )


@router.post("/alerts/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Resolve an alert.

    Args:
        alert_id: Alert ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Resolved alert

    Raises:
        HTTPException: If alert not found or no permission
    """
    user_id = current_user["id"]

    # Get user's organizations
    org_result = await db.execute(
        select(OrganizationMember.organization_id).where(
            OrganizationMember.user_id == user_id
        )
    )
    org_ids = [row[0] for row in org_result.fetchall()]

    # Get alert
    result = await db.execute(
        select(Alert).where(
            Alert.id == alert_id,
            Alert.organization_id.in_(org_ids) if org_ids else False
        )
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    # Resolve alert
    from datetime import datetime
    alert.resolved = True
    alert.resolved_at = datetime.utcnow()

    await db.commit()
    await db.refresh(alert)

    # Get server hostname
    server_result = await db.execute(
        select(Server.hostname).where(Server.id == alert.server_id)
    )
    hostname = server_result.scalar_one_or_none()

    return AlertResponse(
        id=alert.id,
        server_id=alert.server_id,
        server_hostname=hostname,
        organization_id=alert.organization_id,
        type=alert.type,
        severity=alert.severity,
        title=alert.title,
        message=alert.message,
        value=alert.value,
        threshold=alert.threshold,
        resolved=alert.resolved,
        resolved_at=alert.resolved_at.isoformat() if alert.resolved_at else None,
        created_at=alert.created_at.isoformat(),
        updated_at=alert.updated_at.isoformat(),
    )


@router.delete("/alerts/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Delete an alert.

    Args:
        alert_id: Alert ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        204 No Content

    Raises:
        HTTPException: If alert not found or no permission
    """
    user_id = current_user["id"]

    # Get user's organizations
    org_result = await db.execute(
        select(OrganizationMember.organization_id).where(
            OrganizationMember.user_id == user_id
        )
    )
    org_ids = [row[0] for row in org_result.fetchall()]

    # Get alert
    result = await db.execute(
        select(Alert).where(
            Alert.id == alert_id,
            Alert.organization_id.in_(org_ids) if org_ids else False
        )
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    # Delete alert
    await db.delete(alert)
    await db.commit()


@router.get("/alerts/stats", response_model=AlertStatsResponse)
async def get_alert_stats(
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get alert statistics.

    Args:
        start: Start date filter (ISO format)
        end: End date filter (ISO format)
        db: Database session
        current_user: Current authenticated user

    Returns:
        Alert statistics
    """
    user_id = current_user["id"]

    # Get user's organizations
    org_result = await db.execute(
        select(OrganizationMember.organization_id).where(
            OrganizationMember.user_id == user_id
        )
    )
    org_ids = [row[0] for row in org_result.fetchall()]

    if not org_ids:
        return AlertStatsResponse(
            total=0,
            active=0,
            resolved=0,
            critical=0,
            warning=0,
            info=0,
        )

    # Build base query
    query = select(Alert).where(Alert.organization_id.in_(org_ids))

    # Apply date filters
    if start:
        from datetime import datetime
        start_date = datetime.fromisoformat(start)
        query = query.where(Alert.created_at >= start_date)
    if end:
        from datetime import datetime
        end_date = datetime.fromisoformat(end)
        query = query.where(Alert.created_at <= end_date)

    # Get total count
    total_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = total_result.scalar() or 0

    # Get active count
    active_result = await db.execute(
        select(func.count()).select_from(
            query.where(Alert.resolved == False).subquery()
        )
    )
    active = active_result.scalar() or 0

    # Get resolved count
    resolved = total - active

    # Get severity counts
    critical_result = await db.execute(
        select(func.count()).select_from(
            query.where(Alert.severity == "critical").subquery()
        )
    )
    critical = critical_result.scalar() or 0

    warning_result = await db.execute(
        select(func.count()).select_from(
            query.where(Alert.severity == "warning").subquery()
        )
    )
    warning = warning_result.scalar() or 0

    info_result = await db.execute(
        select(func.count()).select_from(
            query.where(Alert.severity == "info").subquery()
        )
    )
    info = info_result.scalar() or 0

    return AlertStatsResponse(
        total=total,
        active=active,
        resolved=resolved,
        critical=critical,
        warning=warning,
        info=info,
    )
