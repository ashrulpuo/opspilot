"""Infrastructure Registry API — domains, SSL certs, DB services, credentials."""
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.asset_encryption import encrypt_secret, decrypt_secret
from app.models.registry import (
    RegistryDomain, RegistrySslCert, RegistryDbService,
    RegistryCredential, RegistryAuditLog,
)
from app.models.organization import OrganizationMember

router = APIRouter(prefix="/registry")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _id() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.utcnow()


async def _org_id(user, db: AsyncSession) -> str:
    r = await db.execute(
        select(OrganizationMember.organization_id)
        .where(OrganizationMember.user_id == user.id)
        .limit(1)
    )
    val = r.scalar_one_or_none()
    if not val:
        raise HTTPException(status_code=403, detail="No organization")
    return val


async def _write_audit(
    db: AsyncSession, org_id: str, user_id: str,
    asset_type: str, asset_id: str, action: str, ip: Optional[str] = None,
):
    log = RegistryAuditLog(
        id=_id(), organization_id=org_id, user_id=user_id,
        asset_type=asset_type, asset_id=asset_id, action=action,
        ip_address=ip, created_at=_now(),
    )
    db.add(log)
    await db.commit()


# ── Schemas ───────────────────────────────────────────────────────────────────

class DomainCreate(BaseModel):
    name: str
    registrar: Optional[str] = None
    registered_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    auto_renew: bool = False
    nameservers: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[str] = None
    server_id: Optional[str] = None


class DomainResponse(BaseModel):
    id: str
    org_id: str
    server_id: Optional[str]
    name: str
    registrar: Optional[str]
    registered_at: Optional[datetime]
    expires_at: Optional[datetime]
    auto_renew: bool
    nameservers: Optional[str]
    notes: Optional[str]
    tags: Optional[str]
    created_at: datetime


class SslCertCreate(BaseModel):
    domain_name: str
    domain_id: Optional[str] = None
    common_name: Optional[str] = None
    issuer: Optional[str] = None
    issued_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    fingerprint: Optional[str] = None
    auto_renew: bool = False
    provider: Optional[str] = None
    notes: Optional[str] = None


class SslCertResponse(BaseModel):
    id: str
    org_id: str
    domain_id: Optional[str]
    domain_name: str
    common_name: Optional[str]
    issuer: Optional[str]
    issued_at: Optional[datetime]
    expires_at: Optional[datetime]
    fingerprint: Optional[str]
    auto_renew: bool
    provider: Optional[str]
    notes: Optional[str]
    created_at: datetime


class DbServiceCreate(BaseModel):
    name: str
    db_type: str = "postgres"
    host: str
    port: Optional[int] = None
    database_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    environment: str = "prod"
    ssl_enabled: bool = False
    notes: Optional[str] = None
    tags: Optional[str] = None
    server_id: Optional[str] = None


class DbServiceResponse(BaseModel):
    id: str
    org_id: str
    server_id: Optional[str]
    name: str
    db_type: str
    host: str
    port: Optional[int]
    database_name: Optional[str]
    username: Optional[str]
    has_password: bool
    environment: str
    ssl_enabled: bool
    notes: Optional[str]
    tags: Optional[str]
    created_at: datetime


class CredentialCreate(BaseModel):
    name: str
    credential_type: str = "web_login"
    url: Optional[str] = None
    username: Optional[str] = None
    secret: Optional[str] = None
    environment: str = "prod"
    notes: Optional[str] = None
    tags: Optional[str] = None
    server_id: Optional[str] = None


class CredentialResponse(BaseModel):
    id: str
    org_id: str
    server_id: Optional[str]
    name: str
    credential_type: str
    url: Optional[str]
    username: Optional[str]
    has_secret: bool
    environment: str
    notes: Optional[str]
    tags: Optional[str]
    created_at: datetime


class AuditLogResponse(BaseModel):
    id: str
    user_id: Optional[str]
    asset_type: str
    asset_id: str
    action: str
    ip_address: Optional[str]
    created_at: datetime


class RevealResponse(BaseModel):
    value: str


# ── Domains ───────────────────────────────────────────────────────────────────

@router.get("/domains", response_model=List[DomainResponse])
async def list_domains(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    org_id = await _org_id(user, db)
    r = await db.execute(
        select(RegistryDomain).where(RegistryDomain.organization_id == org_id)
        .order_by(RegistryDomain.created_at.desc())
    )
    return [_domain_resp(d) for d in r.scalars().all()]


@router.post("/domains", response_model=DomainResponse, status_code=201)
async def create_domain(data: DomainCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    org_id = await _org_id(user, db)
    now = _now()
    d = RegistryDomain(id=_id(), organization_id=org_id, created_at=now, updated_at=now, **data.model_dump())
    db.add(d)
    await db.commit()
    await db.refresh(d)
    await _write_audit(db, org_id, user.id, "domain", d.id, "create")
    return _domain_resp(d)


@router.put("/domains/{domain_id}", response_model=DomainResponse)
async def update_domain(domain_id: str, data: DomainCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    org_id = await _org_id(user, db)
    d = await _get_or_404(RegistryDomain, domain_id, org_id, db)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(d, k, v)
    d.updated_at = _now()
    await db.commit()
    await db.refresh(d)
    await _write_audit(db, org_id, user.id, "domain", d.id, "update")
    return _domain_resp(d)


@router.delete("/domains/{domain_id}", status_code=204)
async def delete_domain(domain_id: str, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    org_id = await _org_id(user, db)
    d = await _get_or_404(RegistryDomain, domain_id, org_id, db)
    await db.delete(d)
    await db.commit()
    await _write_audit(db, org_id, user.id, "domain", domain_id, "delete")


# ── SSL Certs ─────────────────────────────────────────────────────────────────

@router.get("/ssl-certs", response_model=List[SslCertResponse])
async def list_ssl_certs(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    org_id = await _org_id(user, db)
    r = await db.execute(
        select(RegistrySslCert).where(RegistrySslCert.organization_id == org_id)
        .order_by(RegistrySslCert.created_at.desc())
    )
    return [_ssl_resp(c) for c in r.scalars().all()]


@router.post("/ssl-certs", response_model=SslCertResponse, status_code=201)
async def create_ssl_cert(data: SslCertCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    org_id = await _org_id(user, db)
    now = _now()
    c = RegistrySslCert(id=_id(), organization_id=org_id, created_at=now, updated_at=now, **data.model_dump())
    db.add(c)
    await db.commit()
    await db.refresh(c)
    await _write_audit(db, org_id, user.id, "ssl_cert", c.id, "create")
    return _ssl_resp(c)


@router.put("/ssl-certs/{cert_id}", response_model=SslCertResponse)
async def update_ssl_cert(cert_id: str, data: SslCertCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    org_id = await _org_id(user, db)
    c = await _get_or_404(RegistrySslCert, cert_id, org_id, db)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    c.updated_at = _now()
    await db.commit()
    await db.refresh(c)
    await _write_audit(db, org_id, user.id, "ssl_cert", c.id, "update")
    return _ssl_resp(c)


@router.delete("/ssl-certs/{cert_id}", status_code=204)
async def delete_ssl_cert(cert_id: str, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    org_id = await _org_id(user, db)
    c = await _get_or_404(RegistrySslCert, cert_id, org_id, db)
    await db.delete(c)
    await db.commit()
    await _write_audit(db, org_id, user.id, "ssl_cert", cert_id, "delete")


# ── DB Services ───────────────────────────────────────────────────────────────

@router.get("/databases", response_model=List[DbServiceResponse])
async def list_databases(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    org_id = await _org_id(user, db)
    r = await db.execute(
        select(RegistryDbService).where(RegistryDbService.organization_id == org_id)
        .order_by(RegistryDbService.created_at.desc())
    )
    return [_db_resp(s) for s in r.scalars().all()]


@router.post("/databases", response_model=DbServiceResponse, status_code=201)
async def create_database(data: DbServiceCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    org_id = await _org_id(user, db)
    now = _now()
    dump = data.model_dump()
    password = dump.pop("password", None)
    s = RegistryDbService(
        id=_id(), organization_id=org_id, created_at=now, updated_at=now,
        password_enc=encrypt_secret(password) if password else None,
        **dump,
    )
    db.add(s)
    await db.commit()
    await db.refresh(s)
    await _write_audit(db, org_id, user.id, "database", s.id, "create")
    return _db_resp(s)


@router.put("/databases/{db_id}", response_model=DbServiceResponse)
async def update_database(db_id: str, data: DbServiceCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    org_id = await _org_id(user, db)
    s = await _get_or_404(RegistryDbService, db_id, org_id, db)
    dump = data.model_dump(exclude_unset=True)
    password = dump.pop("password", None)
    for k, v in dump.items():
        setattr(s, k, v)
    if password is not None:
        s.password_enc = encrypt_secret(password)
    s.updated_at = _now()
    await db.commit()
    await db.refresh(s)
    await _write_audit(db, org_id, user.id, "database", s.id, "update")
    return _db_resp(s)


@router.get("/databases/{db_id}/reveal", response_model=RevealResponse)
async def reveal_database_password(
    db_id: str, request: Request,
    user=Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    org_id = await _org_id(user, db)
    s = await _get_or_404(RegistryDbService, db_id, org_id, db)
    if not s.password_enc:
        raise HTTPException(status_code=404, detail="No password stored")
    value = decrypt_secret(s.password_enc)
    await _write_audit(db, org_id, user.id, "database", db_id, "reveal",
                       ip=request.client.host if request.client else None)
    return RevealResponse(value=value)


@router.delete("/databases/{db_id}", status_code=204)
async def delete_database(db_id: str, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    org_id = await _org_id(user, db)
    s = await _get_or_404(RegistryDbService, db_id, org_id, db)
    await db.delete(s)
    await db.commit()
    await _write_audit(db, org_id, user.id, "database", db_id, "delete")


# ── Credentials ───────────────────────────────────────────────────────────────

@router.get("/credentials", response_model=List[CredentialResponse])
async def list_credentials(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    org_id = await _org_id(user, db)
    r = await db.execute(
        select(RegistryCredential).where(RegistryCredential.organization_id == org_id)
        .order_by(RegistryCredential.created_at.desc())
    )
    return [_cred_resp(c) for c in r.scalars().all()]


@router.post("/credentials", response_model=CredentialResponse, status_code=201)
async def create_credential(data: CredentialCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    org_id = await _org_id(user, db)
    now = _now()
    dump = data.model_dump()
    secret = dump.pop("secret", None)
    c = RegistryCredential(
        id=_id(), organization_id=org_id, created_at=now, updated_at=now,
        secret_enc=encrypt_secret(secret) if secret else None,
        **dump,
    )
    db.add(c)
    await db.commit()
    await db.refresh(c)
    await _write_audit(db, org_id, user.id, "credential", c.id, "create")
    return _cred_resp(c)


@router.put("/credentials/{cred_id}", response_model=CredentialResponse)
async def update_credential(cred_id: str, data: CredentialCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    org_id = await _org_id(user, db)
    c = await _get_or_404(RegistryCredential, cred_id, org_id, db)
    dump = data.model_dump(exclude_unset=True)
    secret = dump.pop("secret", None)
    for k, v in dump.items():
        setattr(c, k, v)
    if secret is not None:
        c.secret_enc = encrypt_secret(secret)
    c.updated_at = _now()
    await db.commit()
    await db.refresh(c)
    await _write_audit(db, org_id, user.id, "credential", c.id, "update")
    return _cred_resp(c)


@router.get("/credentials/{cred_id}/reveal", response_model=RevealResponse)
async def reveal_credential_secret(
    cred_id: str, request: Request,
    user=Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    org_id = await _org_id(user, db)
    c = await _get_or_404(RegistryCredential, cred_id, org_id, db)
    if not c.secret_enc:
        raise HTTPException(status_code=404, detail="No secret stored")
    value = decrypt_secret(c.secret_enc)
    await _write_audit(db, org_id, user.id, "credential", cred_id, "reveal",
                       ip=request.client.host if request.client else None)
    return RevealResponse(value=value)


@router.delete("/credentials/{cred_id}", status_code=204)
async def delete_credential(cred_id: str, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    org_id = await _org_id(user, db)
    c = await _get_or_404(RegistryCredential, cred_id, org_id, db)
    await db.delete(c)
    await db.commit()
    await _write_audit(db, org_id, user.id, "credential", cred_id, "delete")


# ── Audit log ─────────────────────────────────────────────────────────────────

@router.get("/audit-log", response_model=List[AuditLogResponse])
async def get_audit_log(
    asset_id: Optional[str] = None,
    user=Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    org_id = await _org_id(user, db)
    q = select(RegistryAuditLog).where(RegistryAuditLog.organization_id == org_id)
    if asset_id:
        q = q.where(RegistryAuditLog.asset_id == asset_id)
    q = q.order_by(RegistryAuditLog.created_at.desc()).limit(200)
    r = await db.execute(q)
    return [AuditLogResponse(
        id=l.id, user_id=l.user_id, asset_type=l.asset_type, asset_id=l.asset_id,
        action=l.action, ip_address=l.ip_address, created_at=l.created_at,
    ) for l in r.scalars().all()]


# ── Search ────────────────────────────────────────────────────────────────────

@router.get("/search")
async def search_registry(q: str = "", user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    org_id = await _org_id(user, db)
    term = f"%{q}%"
    results = []

    r = await db.execute(
        select(RegistryDomain).where(
            RegistryDomain.organization_id == org_id,
            or_(RegistryDomain.name.ilike(term), RegistryDomain.registrar.ilike(term)),
        ).limit(10)
    )
    for d in r.scalars().all():
        results.append({"type": "domain", "id": d.id, "name": d.name, "subtitle": d.registrar or ""})

    r = await db.execute(
        select(RegistryDbService).where(
            RegistryDbService.organization_id == org_id,
            or_(RegistryDbService.name.ilike(term), RegistryDbService.host.ilike(term)),
        ).limit(10)
    )
    for s in r.scalars().all():
        results.append({"type": "database", "id": s.id, "name": s.name, "subtitle": f"{s.db_type} · {s.host}"})

    r = await db.execute(
        select(RegistryCredential).where(
            RegistryCredential.organization_id == org_id,
            or_(RegistryCredential.name.ilike(term), RegistryCredential.username.ilike(term)),
        ).limit(10)
    )
    for c in r.scalars().all():
        results.append({"type": "credential", "id": c.id, "name": c.name, "subtitle": c.credential_type})

    return results


# ── Internal helpers ──────────────────────────────────────────────────────────

async def _get_or_404(model, item_id: str, org_id: str, db: AsyncSession):
    r = await db.execute(
        select(model).where(model.id == item_id, model.organization_id == org_id)
    )
    obj = r.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    return obj


def _domain_resp(d: RegistryDomain) -> DomainResponse:
    return DomainResponse(
        id=d.id, org_id=d.organization_id, server_id=d.server_id,
        name=d.name, registrar=d.registrar, registered_at=d.registered_at,
        expires_at=d.expires_at, auto_renew=d.auto_renew,
        nameservers=d.nameservers, notes=d.notes, tags=d.tags,
        created_at=d.created_at,
    )


def _ssl_resp(c: RegistrySslCert) -> SslCertResponse:
    return SslCertResponse(
        id=c.id, org_id=c.organization_id, domain_id=c.domain_id,
        domain_name=c.domain_name, common_name=c.common_name, issuer=c.issuer,
        issued_at=c.issued_at, expires_at=c.expires_at, fingerprint=c.fingerprint,
        auto_renew=c.auto_renew, provider=c.provider, notes=c.notes,
        created_at=c.created_at,
    )


def _db_resp(s: RegistryDbService) -> DbServiceResponse:
    return DbServiceResponse(
        id=s.id, org_id=s.organization_id, server_id=s.server_id,
        name=s.name, db_type=s.db_type, host=s.host, port=s.port,
        database_name=s.database_name, username=s.username,
        has_password=bool(s.password_enc),
        environment=s.environment, ssl_enabled=s.ssl_enabled,
        notes=s.notes, tags=s.tags, created_at=s.created_at,
    )


def _cred_resp(c: RegistryCredential) -> CredentialResponse:
    return CredentialResponse(
        id=c.id, org_id=c.organization_id, server_id=c.server_id,
        name=c.name, credential_type=c.credential_type, url=c.url,
        username=c.username, has_secret=bool(c.secret_enc),
        environment=c.environment, notes=c.notes, tags=c.tags,
        created_at=c.created_at,
    )
