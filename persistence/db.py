from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from app.config.config import settings


engine = create_async_engine(settings.DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class Base(DeclarativeBase):
    pass
