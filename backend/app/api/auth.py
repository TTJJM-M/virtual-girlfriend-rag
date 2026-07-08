from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_db
from app.schemas.auth import (
    RegisterRequest, LoginRequest, RefreshTokenRequest,
    ChangePasswordRequest, TokenResponse, UserInfo
)
from app.services.auth_service import AuthService, init_admin_user
from app.core.security import create_access_token, create_refresh_token
from app.models.user import User
from app.core.deps import get_current_user
from typing import Annotated

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register", response_model=TokenResponse)
async def register(
    req: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    """用户注册"""
    auth = AuthService(db)
    user = await auth.register(req.username, req.email, req.password)

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserInfo(id=user.id, username=user.username, email=user.email, role=user.role.value),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    req: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    """用户登录"""
    auth = AuthService(db)
    user, access_token, refresh_token = await auth.login(req.username, req.password)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserInfo(id=user.id, username=user.username, email=user.email, role=user.role.value),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    req: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    """刷新 token"""
    auth = AuthService(db)
    new_access, new_refresh = await auth.refresh_tokens(req.refresh_token)

    # Get user info
    from app.core.security import decode_token
    payload = decode_token(new_access)
    user_id = payload.get("sub")
    from sqlalchemy import select
    from app.models.user import User
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        user=UserInfo(id=user.id, username=user.username, email=user.email, role=user.role.value),
    )


@router.put("/password")
async def change_password(
    req: ChangePasswordRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    """修改密码"""
    auth = AuthService(db)
    await auth.change_password(current_user, req.old_password, req.new_password)
    return {"message": "密码修改成功"}


@router.get("/me", response_model=UserInfo)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """获取当前用户信息"""
    return UserInfo(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role.value,
    )
