from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_user_by_email,
    hash_password,
    persist_refresh_token,
    revoke_active_refresh_tokens,
    rotate_refresh_token,
    verify_password,
)
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    TokenPair,
    UserCreate,
    UserRead,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserCreate, session: AsyncSession = Depends(get_db)) -> UserRead:
    existing_user = await get_user_by_email(session, payload.email)
    if existing_user is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(email=payload.email, password_hash=hash_password(payload.password))
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return UserRead.model_validate(user)


@router.post("/login", response_model=TokenPair)
async def login_user(payload: LoginRequest, session: AsyncSession = Depends(get_db)) -> TokenPair:
    user = await get_user_by_email(session, payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    await revoke_active_refresh_tokens(session, user.id)
    access_token = create_access_token(user.email)
    refresh_token, token_id, expires_at = create_refresh_token(user.email)
    await persist_refresh_token(session, user, token_id, refresh_token, expires_at)
    await session.commit()

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        access_token_expires_in=get_token_seconds(expires_at=None, kind="access"),
        refresh_token_expires_in=get_token_seconds(expires_at=expires_at, kind="refresh"),
    )


@router.post("/refresh", response_model=TokenPair)
async def refresh_access_token(
    payload: RefreshRequest,
    session: AsyncSession = Depends(get_db),
) -> TokenPair:
    user = await rotate_refresh_token(session, payload.refresh_token)
    access_token = create_access_token(user.email)
    refresh_token, token_id, expires_at = create_refresh_token(user.email)
    await persist_refresh_token(session, user, token_id, refresh_token, expires_at)
    await session.commit()

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        access_token_expires_in=get_token_seconds(expires_at=None, kind="access"),
        refresh_token_expires_in=get_token_seconds(expires_at=expires_at, kind="refresh"),
    )


@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)


def get_token_seconds(expires_at: datetime | None, kind: str) -> int:
    if kind == "access":
        from app.config import get_settings

        return get_settings().access_token_ttl_minutes * 60

    if expires_at is None:
        raise ValueError("expires_at is required for refresh tokens")

    now = datetime.now(timezone.utc)
    return max(int((expires_at - now).total_seconds()), 0)
