from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User, UserRole
from app.core.security import get_password_hash, verify_password
from app.core.exceptions import ConflictException, UnauthorizedException, BadRequestException
from app.config import settings
from app.core.security import create_access_token, create_refresh_token


class AuthService:
    """Authentication service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, username: str, email: str, password: str) -> User:
        """Register new user"""
        # Check if username exists
        result = await self.db.execute(select(User).where(User.username == username))
        if result.scalar_one_or_none():
            raise ConflictException("用户名已存在")

        # Check if email exists
        result = await self.db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            raise ConflictException("邮箱已被注册")

        # Create user
        user = User(
            username=username,
            email=email,
            password_hash=get_password_hash(password),
            role=UserRole.USER,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def login(self, username: str, password: str) -> tuple[User, str, str]:
        """Login and return user + tokens"""
        result = await self.db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedException("用户名或密码错误")

        if not user.is_active:
            raise BadRequestException("账号已被停用")

        # Generate tokens
        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})

        return user, access_token, refresh_token

    async def change_password(self, user: User, old_password: str, new_password: str) -> User:
        """Change password"""
        if not verify_password(old_password, user.password_hash):
            raise BadRequestException("原密码错误")

        user.password_hash = get_password_hash(new_password)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def refresh_tokens(self, refresh_token: str) -> tuple[str, str]:
        """Refresh access token"""
        from app.core.security import decode_token
        from datetime import datetime

        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise UnauthorizedException("Refresh token 无效")

        user_id = payload.get("sub")
        result = await self.db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise UnauthorizedException("用户不存在或已停用")

        # Generate new tokens
        new_access_token = create_access_token({"sub": str(user.id)})
        new_refresh_token = create_refresh_token({"sub": str(user.id)})

        return new_access_token, new_refresh_token


async def init_admin_user(db: AsyncSession):
    """Initialize admin user if not exists (async)"""
    result = await db.execute(select(User).where(User.username == settings.ADMIN_USERNAME))
    admin = result.scalar_one_or_none()

    if not admin:
        admin = User(
            username=settings.ADMIN_USERNAME,
            email="admin@virtual-girlfriend.local",
            password_hash=get_password_hash(settings.ADMIN_PASSWORD),
            role=UserRole.ADMIN,
        )
        db.add(admin)
        await db.commit()
        print(f"✓ Admin user created: {settings.ADMIN_USERNAME}/{settings.ADMIN_PASSWORD}")
    else:
        print(f"✓ Admin user already exists")


def init_admin_user_sync(db):
    """Initialize admin user if not exists (sync)"""
    from sqlalchemy.orm import Session
    result = db.execute(select(User).where(User.username == settings.ADMIN_USERNAME))
    admin = result.scalar_one_or_none()

    if not admin:
        admin = User(
            username=settings.ADMIN_USERNAME,
            email="admin@virtual-girlfriend.local",
            password_hash=get_password_hash(settings.ADMIN_PASSWORD),
            role=UserRole.ADMIN,
        )
        db.add(admin)
        db.commit()
        print(f"✓ Admin user created: {settings.ADMIN_USERNAME}/{settings.ADMIN_PASSWORD}")
    else:
        print(f"✓ Admin user already exists")
