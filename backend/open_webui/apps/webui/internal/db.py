import asyncio
import json
import os
from contextlib import asynccontextmanager
from typing import Any, Optional

from sqlalchemy import Dialect, types
from sqlalchemy.ext.asyncio import (
    async_scoped_session,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.type_api import _T
from typing_extensions import Self
from sqlalchemy.pool import NullPool


####################################
# Database
####################################

DATABASE_URL = os.environ.get(
    "DATABASE_URL", f"postgresql+asyncpg://postgres:postgres@localhost/owebui"
)

# Replace the postgres:// with postgresql://
if "postgres://" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://")


class JSONField(types.TypeDecorator):
    impl = types.Text
    cache_ok = True

    def process_bind_param(self, value: Optional[_T], dialect: Dialect) -> Any:
        return json.dumps(value)

    def process_result_value(self, value: Optional[_T], dialect: Dialect) -> Any:
        if value is not None:
            return json.loads(value)

    def copy(self, **kw: Any) -> Self:
        return JSONField(self.impl.length)

    def db_value(self, value):
        return json.dumps(value)

    def python_value(self, value):
        if value is not None:
            return json.loads(value)


# Workaround to handle the peewee migration
# This is required to ensure the peewee migration is handled before the alembic migration


SQLALCHEMY_DATABASE_URL = DATABASE_URL
if "sqlite" in SQLALCHEMY_DATABASE_URL:
    engine = create_async_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
    )
else:
    engine = create_async_engine(
        SQLALCHEMY_DATABASE_URL, pool_pre_ping=True, poolclass=NullPool
    )

SessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
)
Base = declarative_base()
Session = async_scoped_session(SessionLocal, scopefunc=asyncio.current_task)


# Dependency
async def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()


get_db = asynccontextmanager(get_session)
