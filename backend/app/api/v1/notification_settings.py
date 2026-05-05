"""Notification settings API endpoints."""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.notification import NotificationRecipient, NotificationSmtpConfig
from app.models.organization import OrganizationMember

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────────────

class SmtpConfigRequest(BaseModel):
    host: str
    port: int = 587
    username: str
    password: str = ""
    from_address: str
    use_tls: bool = True
    enabled: bool = True


class SmtpConfigResponse(BaseModel):
    id: str
    organization_id: str
    host: str
    port: int
    username: str
    from_address: str
    use_tls: bool
    enabled: bool
    # password intentionally omitted


class RecipientRequest(BaseModel):
    email: str
    name: Optional[str] = None
    severity_filter: str = "all"  # 'all', 'critical', 'warning'
    enabled: bool = True


class RecipientResponse(BaseModel):
    id: str
    organization_id: str
    email: str
    name: Optional[str]
    severity_filter: str
    enabled: bool
    created_at: str


class TestEmailRequest(BaseModel):
    to_email: str


# ── Helper ────────────────────────────────────────────────────────────────────

async def _get_user_org_id(db: AsyncSession, user_id: str) -> str:
    result = await db.execute(
        select(OrganizationMember.organization_id)
        .where(OrganizationMember.user_id == user_id)
        .limit(1)
    )
    org_id = result.scalar_one_or_none()
    if not org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No organization found")
    return org_id


# ── SMTP Config ───────────────────────────────────────────────────────────────

@router.get("/notification-settings/smtp", response_model=Optional[SmtpConfigResponse])
async def get_smtp_config(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    org_id = await _get_user_org_id(db, current_user["id"])
    result = await db.execute(
        select(NotificationSmtpConfig).where(NotificationSmtpConfig.organization_id == org_id)
    )
    config = result.scalar_one_or_none()
    if not config:
        return None
    return SmtpConfigResponse(
        id=config.id,
        organization_id=config.organization_id,
        host=config.host,
        port=config.port,
        username=config.username,
        from_address=config.from_address,
        use_tls=config.use_tls,
        enabled=config.enabled,
    )


@router.put("/notification-settings/smtp", response_model=SmtpConfigResponse)
async def save_smtp_config(
    request: SmtpConfigRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    org_id = await _get_user_org_id(db, current_user["id"])
    result = await db.execute(
        select(NotificationSmtpConfig).where(NotificationSmtpConfig.organization_id == org_id)
    )
    config = result.scalar_one_or_none()
    now = datetime.utcnow()

    if config:
        config.host = request.host
        config.port = request.port
        config.username = request.username
        if request.password:
            config.password = request.password
        config.from_address = request.from_address
        config.use_tls = request.use_tls
        config.enabled = request.enabled
        config.updated_at = now
    else:
        config = NotificationSmtpConfig(
            id=str(uuid.uuid4()),
            organization_id=org_id,
            host=request.host,
            port=request.port,
            username=request.username,
            password=request.password,
            from_address=request.from_address,
            use_tls=request.use_tls,
            enabled=request.enabled,
            created_at=now,
            updated_at=now,
        )
        db.add(config)

    await db.commit()
    await db.refresh(config)

    return SmtpConfigResponse(
        id=config.id,
        organization_id=config.organization_id,
        host=config.host,
        port=config.port,
        username=config.username,
        from_address=config.from_address,
        use_tls=config.use_tls,
        enabled=config.enabled,
    )


@router.post("/notification-settings/smtp/test")
async def test_smtp_config(
    request: TestEmailRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    org_id = await _get_user_org_id(db, current_user["id"])
    result = await db.execute(
        select(NotificationSmtpConfig).where(NotificationSmtpConfig.organization_id == org_id)
    )
    config = result.scalar_one_or_none()
    if not config or not config.host:
        raise HTTPException(status_code=400, detail="SMTP not configured")

    from app.core.email import EmailService
    svc = EmailService(
        host=config.host,
        port=config.port,
        username=config.username,
        password=config.password,
        from_address=config.from_address or config.username,
        use_tls=config.use_tls,
    )
    ok = svc.send_email(
        to_emails=[request.to_email],
        subject="OpsPilot — SMTP Test",
        html_content="<p>SMTP configuration is working correctly.</p>",
        text_content="SMTP configuration is working correctly.",
    )
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to send test email — check SMTP credentials")
    return {"message": f"Test email sent to {request.to_email}"}


# ── Recipients ────────────────────────────────────────────────────────────────

@router.get("/notification-settings/recipients", response_model=List[RecipientResponse])
async def list_recipients(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    org_id = await _get_user_org_id(db, current_user["id"])
    result = await db.execute(
        select(NotificationRecipient)
        .where(NotificationRecipient.organization_id == org_id)
        .order_by(NotificationRecipient.created_at)
    )
    recipients = result.scalars().all()
    return [
        RecipientResponse(
            id=r.id,
            organization_id=r.organization_id,
            email=r.email,
            name=r.name,
            severity_filter=r.severity_filter,
            enabled=r.enabled,
            created_at=r.created_at.isoformat() + "Z",
        )
        for r in recipients
    ]


@router.post("/notification-settings/recipients", response_model=RecipientResponse, status_code=201)
async def add_recipient(
    request: RecipientRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    org_id = await _get_user_org_id(db, current_user["id"])

    existing = await db.execute(
        select(NotificationRecipient).where(
            NotificationRecipient.organization_id == org_id,
            NotificationRecipient.email == request.email,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Recipient already exists")

    recipient = NotificationRecipient(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        email=request.email,
        name=request.name,
        severity_filter=request.severity_filter,
        enabled=request.enabled,
        created_at=datetime.utcnow(),
    )
    db.add(recipient)
    await db.commit()
    await db.refresh(recipient)

    return RecipientResponse(
        id=recipient.id,
        organization_id=recipient.organization_id,
        email=recipient.email,
        name=recipient.name,
        severity_filter=recipient.severity_filter,
        enabled=recipient.enabled,
        created_at=recipient.created_at.isoformat() + "Z",
    )


@router.patch("/notification-settings/recipients/{recipient_id}", response_model=RecipientResponse)
async def update_recipient(
    recipient_id: str,
    request: RecipientRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    org_id = await _get_user_org_id(db, current_user["id"])
    result = await db.execute(
        select(NotificationRecipient).where(
            NotificationRecipient.id == recipient_id,
            NotificationRecipient.organization_id == org_id,
        )
    )
    recipient = result.scalar_one_or_none()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")

    recipient.email = request.email
    recipient.name = request.name
    recipient.severity_filter = request.severity_filter
    recipient.enabled = request.enabled
    await db.commit()
    await db.refresh(recipient)

    return RecipientResponse(
        id=recipient.id,
        organization_id=recipient.organization_id,
        email=recipient.email,
        name=recipient.name,
        severity_filter=recipient.severity_filter,
        enabled=recipient.enabled,
        created_at=recipient.created_at.isoformat() + "Z",
    )


@router.delete("/notification-settings/recipients/{recipient_id}", status_code=204)
async def delete_recipient(
    recipient_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    org_id = await _get_user_org_id(db, current_user["id"])
    result = await db.execute(
        select(NotificationRecipient).where(
            NotificationRecipient.id == recipient_id,
            NotificationRecipient.organization_id == org_id,
        )
    )
    recipient = result.scalar_one_or_none()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")

    await db.delete(recipient)
    await db.commit()
