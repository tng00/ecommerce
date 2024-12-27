from datetime import datetime, timedelta
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from passlib.context import CryptContext
from app.persistence.repositories.user_repository import UserRepository
from app.presentation.schemas.auth_schema import CreateUser
from app.config.config import settings



bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def create_user(self, create_user: CreateUser, db: AsyncSession):
        hashed_password = bcrypt_context.hash(create_user.password)
        await self.user_repo.create_user(create_user, hashed_password, db)
        return {"status_code": status.HTTP_201_CREATED, "transaction": "Successful"}

    async def login_user(self, username: str, password: str, db: AsyncSession):
        user = await self.user_repo.get_user_by_username(username, db)
        if not user or not bcrypt_context.verify(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate user",
            )

        expires_delta = timedelta(minutes=20)
        token = self.create_access_token(user.username, user.id, expires_delta)
        return token

    @staticmethod
    def create_access_token(username: str, user_id: int, expires_delta: timedelta):
        to_encode = {"sub": username, "id": user_id, "exp": datetime.now() + expires_delta}
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @staticmethod
    async def get_current_user(token: str):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate user",
            )

    @staticmethod
    async def get_current_user_optional(token: str | None):
        if not token:
            return None
        try:
            return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        except JWTError:
            return None
