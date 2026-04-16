"""Organization CRUD and membership — UUID organizations aligned with SQLAlchemy models."""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import _next_unique_org_slug, _slugify
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.organization import Organization, OrganizationMember

router = APIRouter()


# --- Request / response schemas (UUID string ids, aligned with frontend types) ---


class OrganizationCreateRequest(BaseModel):
    """Create organization (description stored only in API layer until DB column exists)."""

    name: str = Field(..., min_length=1, max_length=200)
    slug: Optional[str] = None
    description: Optional[str] = None


class OrganizationUpdateRequest(BaseModel):
    """Patch organization."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    slug: Optional[str] = None
    description: Optional[str] = None


class OrganizationResponse(BaseModel):
    """Single organization JSON."""

    id: str
    name: str
    slug: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    created_by: str = ""
    created_at: str
    updated_at: str


class OrganizationsListResponse(BaseModel):
    """Paginated list matching frontend PaginatedResponse shape."""

    items: List[OrganizationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


def _org_to_response(org: Organization, created_by: str = "") -> OrganizationResponse:
    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        description=None,
        logo_url=None,
        created_by=created_by,
        created_at=org.created_at.isoformat() if org.created_at else "",
        updated_at=org.updated_at.isoformat() if org.updated_at else "",
    )


async def _get_membership(
    db: AsyncSession,
    user_id: str,
    organization_id: str,
) -> Optional[OrganizationMember]:
    r = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.user_id == user_id,
            OrganizationMember.organization_id == organization_id,
        )
    )
    return r.scalar_one_or_none()


async def _require_member(
    db: AsyncSession,
    user_id: str,
    organization_id: str,
) -> OrganizationMember:
    m = await _get_membership(db, user_id, organization_id)
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return m


async def _require_admin(
    db: AsyncSession,
    user_id: str,
    organization_id: str,
) -> OrganizationMember:
    m = await _require_member(db, user_id, organization_id)
    if m.role not in ("admin", "owner"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or owner role required",
        )
    return m


@router.get("", response_model=OrganizationsListResponse)
async def list_organizations(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """Organizations the current user belongs to."""
    user_id = current_user["id"]

    count_q = (
        select(func.count())
        .select_from(OrganizationMember)
        .where(OrganizationMember.user_id == user_id)
    )
    total = (await db.execute(count_q)).scalar_one()

    offset = (page - 1) * page_size
    q = (
        select(Organization)
        .join(OrganizationMember, OrganizationMember.organization_id == Organization.id)
        .where(OrganizationMember.user_id == user_id)
        .order_by(Organization.name.asc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(q)
    orgs = result.scalars().all()

    items = [_org_to_response(o, created_by=user_id) for o in orgs]
    total_pages = max(1, (total + page_size - 1) // page_size) if total else 1

    return OrganizationsListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    body: OrganizationCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Create organization and add current user as admin."""
    user_id = current_user["id"]

    base_slug = (body.slug or "").strip() or _slugify(body.name)
    slug = await _next_unique_org_slug(db, base_slug)

    org_id = str(uuid.uuid4())
    now = datetime.utcnow()
    org = Organization(
        id=org_id,
        name=body.name.strip(),
        slug=slug,
        created_at=now,
        updated_at=now,
    )
    member = OrganizationMember(
        user_id=user_id,
        organization_id=org_id,
        role="admin",
    )
    db.add(org)
    db.add(member)
    await db.commit()
    await db.refresh(org)

    return _org_to_response(org, created_by=user_id)


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    user_id = current_user["id"]
    await _require_member(db, user_id, org_id)
    r = await db.execute(select(Organization).where(Organization.id == org_id))
    org = r.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return _org_to_response(org, created_by=user_id)


@router.put("/{org_id}", response_model=OrganizationResponse)
@router.patch("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: str,
    body: OrganizationUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    user_id = current_user["id"]
    await _require_admin(db, user_id, org_id)
    r = await db.execute(select(Organization).where(Organization.id == org_id))
    org = r.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    if body.name is not None:
        org.name = body.name.strip()
    if body.slug is not None:
        new_slug = _slugify(body.slug)
        dup = await db.execute(select(Organization.id).where(Organization.slug == new_slug, Organization.id != org_id))
        if dup.scalar_one_or_none() is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Slug already in use")
        org.slug = new_slug
    org.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(org)
    return _org_to_response(org, created_by=user_id)


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    org_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    user_id = current_user["id"]
    await _require_admin(db, user_id, org_id)
    r = await db.execute(select(Organization).where(Organization.id == org_id))
    org = r.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    await db.delete(org)
    await db.commit()
    return None


@router.post("/{org_id}/switch", status_code=status.HTTP_200_OK)
async def switch_organization(
    org_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Client-side org context only; verify membership then acknowledge."""
    user_id = current_user["id"]
    await _require_member(db, user_id, org_id)
    return {"ok": True, "organization_id": org_id}


# Static path must not be shadowed: add by-slug if needed later below get /{org_id}
