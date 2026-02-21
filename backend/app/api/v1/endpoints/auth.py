"""Authentication endpoints: register, login, profile."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)


async def get_authenticated_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate user from JWT bearer token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    user_id = decode_access_token(credentials.credentials)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user = await db.get(User, uuid.UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    # Check if email exists
    stmt = select(User).where(User.email == request.email)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=request.email,
        hashed_password=hash_password(request.password),
        full_name=request.full_name,
    )
    db.add(user)
    await db.flush()

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email and password."""
    stmt = select(User).where(User.email == request.email)
    user = (await db.execute(stmt)).scalar_one_or_none()

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def get_profile(user: User = Depends(get_authenticated_user)):
    """Get current user profile."""
    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at.isoformat(),
    )
