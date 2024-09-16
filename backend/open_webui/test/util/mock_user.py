from contextlib import contextmanager, asynccontextmanager

from fastapi import FastAPI
from fastapi.testclient import TestClient


@asynccontextmanager
async def mock_webui_user(**kwargs):
    from open_webui.apps.webui.main import app

    async with mock_user(app, **kwargs) as client:
        yield client


@asynccontextmanager
async def mock_user(app: FastAPI, **kwargs):
    from open_webui.utils.utils import (
        get_current_user,
        get_verified_user,
        get_admin_user,
        get_current_user_by_api_key,
    )
    from open_webui.apps.webui.models.users import User

    def create_user():
        user_parameters = {
            "id": "1",
            "name": "John Doe",
            "email": "john.doe@openwebui.com",
            "role": "user",
            "profile_image_url": "/user.png",
            "last_active_at": 1627351200,
            "updated_at": 1627351200,
            "created_at": 162735120,
            **kwargs,
        }
        return User(**user_parameters)

    app.dependency_overrides = {
        get_current_user: create_user,
        get_verified_user: create_user,
        get_admin_user: create_user,
        get_current_user_by_api_key: create_user,
    }
    with TestClient(app) as test_client:
        yield test_client
