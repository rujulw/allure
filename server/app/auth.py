from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.user import RefreshToken, User

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(subject: str) -> str:
    settings = get_settings()
    expires_at = utcnow() + timedelta(minutes=settings.access_token_ttl_minutes)
    payload = {
        "sub": subject,
        "type": "access",
        "jti": str(uuid4()),
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str) -> tuple[str, str, datetime]:
    settings = get_settings()
    token_id = str(uuid4())
    expires_at = utcnow() + timedelta(minutes=settings.refresh_token_ttl_minutes)
    payload = {
        "sub": subject,
        "type": "refresh",
        "jti": token_id,
        "exp": expires_at,
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, token_id, expires_at


def decode_token(token: str) -> dict:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        ) from exc


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    stmt: Select[tuple[User]] = select(User).where(User.email == email)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    email = payload.get("sub")
    if not isinstance(email, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    user = await get_user_by_email(session, email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    return user


async def persist_refresh_token(
    session: AsyncSession,
    user: User,
    token_id: str,
    token: str,
    expires_at: datetime,
) -> RefreshToken:
    refresh = RefreshToken(
        user_id=user.id,
        token_id=token_id,
        token_hash=hash_password(token),
        expires_at=expires_at,
    )
    session.add(refresh)
    await session.flush()
    return refresh


async def revoke_active_refresh_tokens(session: AsyncSession, user_id: int) -> None:
    stmt: Select[tuple[RefreshToken]] = select(RefreshToken).where(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked_at.is_(None),
    )
    result = await session.execute(stmt)
    active_tokens: Sequence[RefreshToken] = result.scalars().all()
    now = utcnow()
    for token in active_tokens:
        token.revoked_at = now


async def rotate_refresh_token(session: AsyncSession, raw_refresh_token: str) -> User:
    payload = decode_token(raw_refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    email = payload.get("sub")
    token_id = payload.get("jti")
    if not isinstance(email, str) or not isinstance(token_id, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    stmt: Select[tuple[RefreshToken]] = select(RefreshToken).where(RefreshToken.token_id == token_id)
    result = await session.execute(stmt)
    refresh = result.scalar_one_or_none()
    if refresh is None or refresh.revoked_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if as_utc(refresh.expires_at) <= utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )

    if not verify_password(raw_refresh_token, refresh.token_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    refresh.revoked_at = utcnow()
    user = await session.get(User, refresh.user_id)
    if user is None or user.email != email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    return user
