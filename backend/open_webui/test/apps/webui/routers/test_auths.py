import uuid

import pytest

from test.util.abstract_integration_test import AbstractPostgresTest
from test.util.mock_user import mock_webui_user
from open_webui.apps.webui.models.auths import Auths
from open_webui.apps.webui.models.users import Users
from utils.utils import get_password_hash


class TestAuths(AbstractPostgresTest):
    BASE_PATH = "/api/v1/auths"
    users = Users
    auths = Auths

    @pytest.mark.asyncio
    async def test_get_session_user(self):
        async with mock_webui_user():
            response = await self.fast_api_client.get(self.create_url())
        assert response.status_code == 307

    @pytest.mark.asyncio
    async def test_update_profile(self, some_user):
        from open_webui.utils.utils import get_password_hash

        async for some_users in some_user:
            user = await some_users(
                email="john.doe@openwebui.com",
                password=get_password_hash("old_password"),
                name="John Doe",
                profile_image_url="/user.png",
                role="user",
            )

            updated = await self.users.update_user_by_id(
                user.id, {"name": "John Doe 2", "email": "johndoes2@gmail.com"}
            )

            assert updated.email == "johndoes2@gmail.com"

    @pytest.mark.asyncio
    async def test_update_password(self, some_user):
        from open_webui.utils.utils import get_password_hash

        async for some_users in some_user:
            user = await some_users(
                email="john.doe@openwebui.com",
                password=get_password_hash("old_password"),
                name="John Doe",
                profile_image_url="/user.png",
                role="user",
            )

            async with mock_webui_user(id=user.id):
                response = await self.fast_api_client.post(
                    self.create_url("/update/password"),
                    json={"password": "old_password", "new_password": "new_password"},
                )
                assert response.status_code == 200

                old_auth = await self.auths.authenticate_user(
                    "john.doe@openwebui.com", "old_password"
                )
                assert old_auth is None
                new_auth = await self.auths.authenticate_user(
                    "john.doe@openwebui.com", "new_password"
                )
                assert new_auth is not None

    @pytest.mark.asyncio
    async def test_signin(self, some_user):
        from open_webui.utils.utils import get_password_hash

        async for some_users in some_user:
            user = await some_users(
                email="john.doe@openwebui.com",
                password=get_password_hash("password"),
                name="John Doe",
                profile_image_url="/user.png",
                role="user",
            )

            async with mock_webui_user(id=user.id):
                response = await self.fast_api_client.post(
                    self.create_url("/signin"),
                    json={"email": "john.doe@openwebui.com", "password": "password"},
                )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_signup(self, some_user):
        response = await self.fast_api_client.post(
            self.create_url("/signup"),
            json={
                "name": "John Doe",
                "email": "john.doe@openwebui.com",
                "password": "password",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] is not None and len(data["id"]) > 0
        assert data["name"] == "John Doe"
        assert data["email"] == "john.doe@openwebui.com"
        assert data["role"] in ["admin", "user", "pending"]
        assert data["profile_image_url"] == "/user.png"
        assert data["token"] is not None and len(data["token"]) > 0
        assert data["token_type"] == "Bearer"
        await self.auths.delete_auth_by_id(data["id"])

    @pytest.mark.asyncio
    async def test_add_user(self, some_user):
        async with mock_webui_user():
            email = f"john.doe@{str(uuid.uuid4().hex)}.com"
            response = await self.fast_api_client.post(
                self.create_url("/add"),
                json={
                    "name": "John Doe New",
                    "email": email,
                    "password": "password",
                    "role": "admin",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["id"] is not None and len(data["id"]) > 0
            assert data["name"] == "John Doe New"
            assert data["email"] == email
            assert data["role"] == "admin"
            assert data["profile_image_url"] == "/user.png"
            assert data["token"] is not None and len(data["token"]) > 0
            assert data["token_type"] == "Bearer"
            await self.auths.delete_auth_by_id(data["id"])

    @pytest.mark.asyncio
    async def test_get_admin_details(self, some_user):
        async for some_users in some_user:
            user = await some_users(
                email="john.doe@openwebui.com",
                password="password",
                name="John Doe",
                profile_image_url="/user.png",
                role="admin",
            )
            async with mock_webui_user(id=user.id):
                response = await self.fast_api_client.get(
                    self.create_url("/admin/details")
                )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_create_api_key_(self, some_user):
        async for some_users in some_user:
            user = await some_users(
                email="john.doe@openwebui.com",
                password=get_password_hash("old_password"),
                name="John Doe",
                profile_image_url="/user.png",
                role="user",
            )
            async with mock_webui_user(id=user.id):
                response = await self.fast_api_client.post(self.create_url("/api_key"))
            assert response.status_code == 200
            data = response.json()
            assert data["api_key"] is not None
            assert len(data["api_key"]) > 0

    @pytest.mark.asyncio
    async def test_delete_api_key(self, some_user):
        async for some_users in some_user:
            user = await some_users(
                email="john.doe@openwebui.com",
                password=get_password_hash("old_password"),
                name="John Doe",
                profile_image_url="/user.png",
                role="user",
            )
            await self.users.update_user_api_key_by_id(user.id, "abc")
            async with mock_webui_user(id=user.id):
                response = await self.fast_api_client.delete(
                    self.create_url("/api_key")
                )
            assert response.status_code == 200
            assert response.json() == True
            db_user = await self.users.get_user_by_id(user.id)
            assert db_user.api_key is None

    @pytest.mark.asyncio
    async def test_get_api_key(self, some_user):
        async for some_users in some_user:
            user = await some_users(
                email="john.doe@openwebui.com",
                password=get_password_hash("old_password"),
                name="John Doe",
                profile_image_url="/user.png",
                role="user",
            )
            await self.users.update_user_api_key_by_id(user.id, "abc")
            async with mock_webui_user(id=user.id):
                response = await self.fast_api_client.get(self.create_url("/api_key"))
            assert response.status_code == 200
            assert response.json() == {"api_key": "abc"}
