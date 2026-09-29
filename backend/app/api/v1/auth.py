from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenPair,
)
from app.services.auth_service import (
    login_user,
    refresh_tokens,
    register_user,
    request_password_reset,
    reset_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, session: AsyncSession = Depends(get_db)) -> TokenPair:
    user = await register_user(session, payload.name, payload.email, payload.password)
    access_token, refresh_token = await refresh_tokens_for_new_user(session, user)
    return TokenPair(access_token=access_token, refresh_token=refresh_token, user=user)


async def refresh_tokens_for_new_user(session: AsyncSession, user):
    from app.services.auth_service import create_token_pair

    access_token, refresh_token = await create_token_pair(session, user)
    await session.commit()
    return access_token, refresh_token


@router.post("/login", response_model=TokenPair)
async def login(
    payload: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> TokenPair:
    ip = request.client.host if request.client else "unknown"
    user, access_token, refresh_token = await login_user(session, payload.email, payload.password, ip)
    return TokenPair(access_token=access_token, refresh_token=refresh_token, user=user)


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, session: AsyncSession = Depends(get_db)) -> TokenPair:
    user, access_token, refresh_token = await refresh_tokens(session, payload.refresh_token)
    return TokenPair(access_token=access_token, refresh_token=refresh_token, user=user)


@router.post("/password/forgot", response_model=MessageResponse)
async def forgot_password(
    payload: ForgotPasswordRequest, session: AsyncSession = Depends(get_db)
) -> MessageResponse:
    await request_password_reset(session, payload.email)
    return MessageResponse(detail="If the account exists, a reset token has been sent.")


@router.post("/password/reset", response_model=MessageResponse)
async def password_reset(
    payload: ResetPasswordRequest, session: AsyncSession = Depends(get_db)
) -> MessageResponse:
    await reset_password(session, payload.token, payload.password)
    return MessageResponse(detail="Password reset complete.")
