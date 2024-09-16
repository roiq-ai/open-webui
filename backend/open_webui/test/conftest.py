from typing import AsyncGenerator
import pytest
from open_webui.apps.webui.internal.db import Base, get_db
from open_webui.apps.webui.models.auths import Auths


@pytest.fixture(autouse=True)
async def db() -> AsyncGenerator:
    async with get_db() as db:
        for table in Base.metadata.tables:
            await db.execute(f"TRUNCATE TABLE {table}")
    yield


@pytest.fixture(scope="function")
async def some_user():
    user_ = []

    async def _some_user(**kwargs):
        user = await Auths.insert_new_auth(**kwargs)
        user_.append(user)
        return user

    try:
        yield _some_user
    finally:
        for user in user_:
            await Auths.delete_auth_by_id(user.id)
