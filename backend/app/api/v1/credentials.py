"""Credential management API endpoints for OpsPilot."""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.vault import vault_client
from app.models.server import Server
from app.models.organization import Organization, OrganizationMember
from app.models.server import CredentialsVaultPath

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================
# Request Schemas
# ============================================

class CreateCredentialRequest(BaseModel):
    """Credential creation request schema."""

    server_id: str
    name: str
    type: str  # "ssh_key", "password", "api_key", "token"
    data: Dict[str, Any]  # Encrypted credential data
    description: Optional[str] = None


class UpdateCredentialRequest(BaseModel):
    """Credential update request schema."""

    name: Optional[str] = None
    description: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


# ============================================
# Response Schemas
# ============================================

class CredentialResponse(BaseModel):
    """Credential response schema."""

    id: str
    server_id: str
    server_hostname: Optional[str]
    name: str
    type: str
    description: Optional[str]
    created_at: str
    updated_at: str


class CredentialsListResponse(BaseModel):
    """Credentials list response schema."""

    total: int
    page: int
    page_size: int
    total_pages: int
    credentials: List[CredentialResponse]


# ============================================
# Endpoints
# ============================================

@router.get("/organizations/{organization_id}/credentials", response_model=CredentialsListResponse)
async def list_credentials(
    organization_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    server_id: Optional[str] = Query(None),
    credential_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """List all credentials in an organization.

    Args:
        organization_id: Organization ID
        page: Page number
        page_size: Items per page
        server_id: Filter by server
        credential_type: Filter by type
        db: Database session
        current_user: Current authenticated user

    Returns:
        Paginated list of credentials

    Raises:
        HTTPException: If no permission to access organization
    """
    user_id = current_user["id"]

    # Verify user has access to organization
    org_member_result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_id
        )
    )
    org_member = org_member_result.scalar_one_or_none()

    if not org_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to access this organization",
        )

    # Build query
    query = (
        select(CredentialsVaultPath, Server.hostname)
        .join(Server, CredentialsVaultPath.server_id == Server.id)
        .where(CredentialsVaultPath.organization_id == organization_id)
    )

    # Apply filters
    if server_id:
        query = query.where(CredentialsVaultPath.server_id == server_id)
    if credential_type:
        # Filter by credential type (stored in description or parsed from path)
        query = query.where(CredentialsVaultPath.path.like(f"%{credential_type}%"))

    # Order by created_at desc
    query = query.order_by(CredentialsVaultPath.created_at.desc())

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Execute query
    results = await db.execute(query)
    credentials_with_hostnames = results.fetchall()

    # Build response
    credentials = []
    for cred, hostname in credentials_with_hostnames:
        # Parse credential type from path or name
        cred_type = "unknown"
        if "ssh" in cred.path.lower():
            cred_type = "ssh_key"
        elif "password" in cred.path.lower():
            cred_type = "password"
        elif "api_key" in cred.path.lower() or "api-key" in cred.path.lower():
            cred_type = "api_key"
        elif "token" in cred.path.lower():
            cred_type = "token"

        credentials.append(
            CredentialResponse(
                id=cred.id,
                server_id=cred.server_id,
                server_hostname=hostname,
                name=cred.path.split("/")[-1],  # Extract name from path
                type=cred_type,
                description=cred.description,
                created_at=cred.created_at.isoformat(),
                updated_at=cred.updated_at.isoformat(),
            )
        )

    total_pages = (total + page_size - 1) // page_size

    return CredentialsListResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        credentials=credentials,
    )


@router.get("/credentials/{credential_id}", response_model=CredentialResponse)
async def get_credential(
    credential_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get a credential by ID.

    Args:
        credential_id: Credential ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Credential details (without sensitive data)

    Raises:
        HTTPException: If credential not found or no permission
    """
    user_id = current_user["id"]

    # Get credential with server info
    query = (
        select(CredentialsVaultPath, Server.hostname, Server.organization_id)
        .join(Server, CredentialsVaultPath.server_id == Server.id)
        .where(CredentialsVaultPath.id == credential_id)
    )
    result = await db.execute(query)
    cred_data = result.fetchone()

    if not cred_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found",
        )

    cred, hostname, org_id = cred_data

    # Verify user has access to organization
    org_member_result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user_id
        )
    )
    org_member = org_member_result.scalar_one_or_none()

    if not org_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to access this credential",
        )

    # Parse credential type
    cred_type = "unknown"
    if "ssh" in cred.path.lower():
        cred_type = "ssh_key"
    elif "password" in cred.path.lower():
        cred_type = "password"
    elif "api_key" in cred.path.lower() or "api-key" in cred.path.lower():
        cred_type = "api_key"
    elif "token" in cred.path.lower():
        cred_type = "token"

    return CredentialResponse(
        id=cred.id,
        server_id=cred.server_id,
        server_hostname=hostname,
        name=cred.path.split("/")[-1],
        type=cred_type,
        description=cred.description,
        created_at=cred.created_at.isoformat(),
        updated_at=cred.updated_at.isoformat(),
    )


@router.post("/organizations/{organization_id}/credentials", response_model=CredentialResponse, status_code=status.HTTP_201_CREATED)
async def create_credential(
    organization_id: str,
    request: CreateCredentialRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Create a new credential (stored in Vault).

    Args:
        organization_id: Organization ID
        request: Credential creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created credential

    Raises:
        HTTPException: If server not found or no permission
    """
    user_id = current_user["id"]

    # Verify user has access to organization
    org_member_result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_id
        )
    )
    org_member = org_member_result.scalar_one_or_none()

    if not org_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to access this organization",
        )

    # Verify server exists and belongs to organization
    server_result = await db.execute(
        select(Server).where(
            Server.id == request.server_id,
            Server.organization_id == organization_id
        )
    )
    server = server_result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )

    # Generate vault path
    import uuid
    vault_path = f"opspilot/{organization_id}/{request.server_id}/{request.name}"

    # Store credential data in Vault
    vault_success = vault_client.write_secret(
        path=vault_path,
        data=request.data
    )

    if not vault_success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store credential in Vault",
        )

    # Create credential record in database (metadata only)
    credential = CredentialsVaultPath(
        id=str(uuid.uuid4()),
        server_id=request.server_id,
        organization_id=organization_id,
        path=vault_path,
        description=request.description,
    )

    db.add(credential)
    await db.commit()
    await db.refresh(credential)

    logger.info(f"Credential created: {vault_path}")

    return CredentialResponse(
        id=credential.id,
        server_id=credential.server_id,
        server_hostname=server.hostname,
        name=request.name,
        type=request.type,
        description=credential.description,
        created_at=credential.created_at.isoformat(),
        updated_at=credential.updated_at.isoformat(),
    )


@router.put("/credentials/{credential_id}", response_model=CredentialResponse)
async def update_credential(
    credential_id: str,
    request: UpdateCredentialRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Update a credential.

    Args:
        credential_id: Credential ID
        request: Credential update data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated credential

    Raises:
        HTTPException: If credential not found or no permission
    """
    user_id = current_user["id"]

    # Get credential
    result = await db.execute(
        select(CredentialsVaultPath, Server.hostname, Server.organization_id)
        .join(Server, CredentialsVaultPath.server_id == Server.id)
        .where(CredentialsVaultPath.id == credential_id)
    )
    cred_data = result.fetchone()

    if not cred_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found",
        )

    cred, hostname, org_id = cred_data

    # Verify user has access to organization
    org_member_result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user_id
        )
    )
    org_member = org_member_result.scalar_one_or_none()

    if not org_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to access this credential",
        )

    # Update credential in Vault
    if request.data:
        vault_success = vault_client.write_secret(
            path=cred.path,
            data=request.data
        )

        if not vault_success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update credential in Vault",
            )

    # Update credential record in database
    update_data = request.model_dump(exclude_unset=True, exclude={"data"})
    for key, value in update_data.items():
        if value is not None:
            setattr(cred, key, value)

    cred.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(cred)

    # Parse credential type
    cred_type = "unknown"
    if "ssh" in cred.path.lower():
        cred_type = "ssh_key"
    elif "password" in cred.path.lower():
        cred_type = "password"
    elif "api_key" in cred.path.lower() or "api-key" in cred.path.lower():
        cred_type = "api_key"
    elif "token" in cred.path.lower():
        cred_type = "token"

    return CredentialResponse(
        id=cred.id,
        server_id=cred.server_id,
        server_hostname=hostname,
        name=cred.path.split("/")[-1],
        type=cred_type,
        description=cred.description,
        created_at=cred.created_at.isoformat(),
        updated_at=cred.updated_at.isoformat(),
    )


@router.delete("/credentials/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credential(
    credential_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Delete a credential.

    Args:
        credential_id: Credential ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        204 No Content

    Raises:
        HTTPException: If credential not found or no permission
    """
    user_id = current_user["id"]

    # Get credential
    result = await db.execute(
        select(CredentialsVaultPath, Server.organization_id)
        .join(Server, CredentialsVaultPath.server_id == Server.id)
        .where(CredentialsVaultPath.id == credential_id)
    )
    cred_data = result.fetchone()

    if not cred_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found",
        )

    cred, org_id = cred_data

    # Verify user has access to organization
    org_member_result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user_id
        )
    )
    org_member = org_member_result.scalar_one_or_none()

    if not org_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to access this credential",
        )

    # Delete credential from Vault
    vault_success = vault_client.delete_secret(
        path=cred.path
    )

    if not vault_success:
        logger.warning(f"Failed to delete credential from Vault: {cred.path}")

    vault_path = cred.path
    logger.info(f"Credential deleted: {vault_path}")

    # Delete credential record from database
    await db.delete(cred)
    await db.commit()


@router.post("/credentials/{credential_id}/rotate", response_model=CredentialResponse)
async def rotate_credential(
    credential_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Rotate a credential (generate new value).

    Args:
        credential_id: Credential ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Rotated credential

    Raises:
        HTTPException: If credential not found or no permission
    """
    user_id = current_user["id"]

    # Get credential
    result = await db.execute(
        select(CredentialsVaultPath, Server.hostname, Server.organization_id)
        .join(Server, CredentialsVaultPath.server_id == Server.id)
        .where(CredentialsVaultPath.id == credential_id)
    )
    cred_data = result.fetchone()

    if not cred_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found",
        )

    cred, hostname, org_id = cred_data

    # Verify user has access to organization
    org_member_result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user_id
        )
    )
    org_member = org_member_result.scalar_one_or_none()

    if not org_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to access this credential",
        )

    # Rotate credential in Vault (generate new value)
    # Read current credential type
    cred_type = "unknown"
    if "ssh" in cred.path.lower():
        cred_type = "ssh_key"
    elif "password" in cred.path.lower():
        cred_type = "password"
    elif "api_key" in cred.path.lower() or "api-key" in cred.path.lower():
        cred_type = "api_key"
    elif "token" in cred.path.lower():
        cred_type = "token"

    # Generate new value based on type
    new_value = ""
    if cred_type in ["password", "api_key", "token"]:
        new_value = vault_client.generate_password(length=32)
    else:
        # For SSH keys, use ssh-keygen (simplified - in production, use proper key generation)
        new_value = vault_client.generate_password(length=64)  # Placeholder

    # Update credential in Vault with new value
    vault_success = vault_client.write_secret(
        path=cred.path,
        data={"value": new_value, "type": cred_type}
    )

    if not vault_success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to rotate credential in Vault",
        )

    cred.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(cred)

    logger.info(f"Credential rotated: {cred.path}")

    # Parse credential type
    cred_type = "unknown"
    if "ssh" in cred.path.lower():
        cred_type = "ssh_key"
    elif "password" in cred.path.lower():
        cred_type = "password"
    elif "api_key" in cred.path.lower() or "api-key" in cred.path.lower():
        cred_type = "api_key"
    elif "token" in cred.path.lower():
        cred_type = "token"

    return CredentialResponse(
        id=cred.id,
        server_id=cred.server_id,
        server_hostname=hostname,
        name=cred.path.split("/")[-1],
        type=cred_type,
        description=cred.description,
        created_at=cred.created_at.isoformat(),
        updated_at=cred.updated_at.isoformat(),
    )
