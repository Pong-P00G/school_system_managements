"""Authentication endpoints (placeholder)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.rate_limit import rate_limit_auth
from app.models.user import User
from app.schemas.user import LoginRequest, TokenResponse, UserCreate, UserOut

router = APIRouter()


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(rate_limit_auth)])
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return JWT token."""
    result = await db.execute(select(User).where(User.username == request.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    token = create_access_token(data={"sub": str(user.user_id), "username": user.username})
    return TokenResponse(access_token=token)


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(rate_limit_auth)])
async def register(request: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    # Check existing
    existing = await db.execute(
        select(User).where((User.username == request.username) | (User.email == request.email))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already registered",
        )

    user = User(
        username=request.username,
        email=request.email,
        password_hash=get_password_hash(request.password),
    )
    db.add(user)
    try:
        await db.flush()
        await db.refresh(user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already registered",
        )
    return user
