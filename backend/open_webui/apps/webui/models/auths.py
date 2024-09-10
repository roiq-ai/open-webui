import logging
import uuid
from typing import Any, Optional

from config import SRC_LOG_LEVELS
from open_webui.apps.webui.internal.db import Base, get_db
from open_webui.apps.webui.models.users import UserModel, Users
from open_webui.utils.utils import verify_password
from pydantic import BaseModel
from sqlalchemy import Boolean, Column, String, Text, delete, select, update

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])

####################
# DB MODEL
####################


class Auth(Base):
    __tablename__ = "auth"

    id = Column(String, primary_key=True)
    email = Column(String)
    password = Column(Text)
    active = Column(Boolean)


class AuthModel(BaseModel):
    id: str
    email: str
    password: str
    active: bool = True


####################
# Forms
####################


class Token(BaseModel):
    token: str
    token_type: str


class ApiKey(BaseModel):
    api_key: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    profile_image_url: str


class SigninResponse(Token, UserResponse):
    pass


class SigninForm(BaseModel):
    email: str
    password: str


class ProfileImageUrlForm(BaseModel):
    profile_image_url: str


class UpdateProfileForm(BaseModel):
    profile_image_url: str
    name: str


class UpdatePasswordForm(BaseModel):
    password: str
    new_password: str


class SignupForm(BaseModel):
    name: str
    email: str
    password: str
    profile_image_url: Optional[str] = "/user.png"


class AddUserForm(SignupForm):
    role: Optional[str] = "pending"


class AuthsTable:
    async def insert_new_auth(
        self,
        email: str,
        password: str,
        name: str,
        profile_image_url: str = "/user.png",
        role: str = "pending",
        oauth_sub: Optional[str] = None,
    ) -> Optional[UserModel]:
        async with get_db() as db:
            log.info("insert_new_auth")

            id = str(uuid.uuid4())

            auth = AuthModel(
                **{"id": id, "email": email, "password": password, "active": True}
            )
            result = Auth(**auth.model_dump())
            db.add(result)

            user = await Users.insert_new_user(
                id, name, email, profile_image_url, role, oauth_sub
            )

            await db.commit()
            await db.refresh(result)

            if result and user:
                return user
            else:
                return None

    async def authenticate_user(self, email: str, password: str) -> Optional[UserModel]:
        log.info(f"authenticate_user: {email}")
        async with get_db() as db:
            stmt = select(Auth).where(*[Auth.email == email, Auth.active == True])
            auth = await db.execute(stmt)
            auth = auth.scalar()
            if auth:
                if verify_password(password, auth.password):
                    user = await Users.get_user_by_id(auth.id)
                    return user
                else:
                    return None
            else:
                return None

    async def authenticate_user_by_api_key(self, api_key: str) -> bool | None | Any:
        log.info(f"authenticate_user_by_api_key: {api_key}")
        # if no api_key, return None
        if not api_key:
            return None

        user = await Users.get_user_by_api_key(api_key)
        return user if user else None

    async def authenticate_user_by_trusted_header(
        self, email: str
    ) -> Optional[UserModel]:
        log.info(f"authenticate_user_by_trusted_header: {email}")
        async with get_db() as db:
            stmt = select(Auth).where(*[Auth.email == email, Auth.active == True])
            auth = await db.execute(stmt)
            auth = auth.scalar()
            if auth:
                user = await Users.get_user_by_id(auth.id)
                return user

    async def update_user_password_by_id(self, id: str, new_password: str) -> bool:
        async with get_db() as db:
            stmt = (
                update(Auth)
                .where(Auth.id == id)
                .values(password=new_password)
                .returning(Auth.id)
            )
            await db.execute(stmt)
            await db.commit()
            return True

    async def update_email_by_id(self, id: str, email: str) -> bool:
        async with get_db() as db:
            stmt = (
                update(Auth).where(Auth.id == id).values(email=email).returning(Auth.id)
            )
            await db.execute(stmt)
            await db.commit()
            return True

    async def delete_auth_by_id(self, id: str) -> bool:
        async with get_db() as db:
            # Delete User
            stmt = delete(Auth).where(Auth.id == id)
            result = await Users.delete_user_by_id(id)

            if result:
                await db.execute(stmt)
                await db.commit()

                return True
            else:
                return False


Auths = AuthsTable()
