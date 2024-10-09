import time
from datetime import datetime, date
from typing import List, Optional, Union
from dateutil.relativedelta import relativedelta
from open_webui.apps.webui.internal.db import Base, JSONField, get_db
from open_webui.apps.webui.models.chats import Chats
from pydantic import BaseModel, ConfigDict
from sqlalchemy import (
    BigInteger,
    Column,
    String,
    Text,
    delete,
    func,
    select,
    update,
    and_,
)
import sqlalchemy.sql.functions as func

####################
# User DB Schema
####################


class User(Base):
    __tablename__ = "user"

    id = Column(String, primary_key=True)
    name = Column(String)
    email = Column(String)
    role = Column(String)
    profile_image_url = Column(Text)

    last_active_at = Column(BigInteger)
    updated_at = Column(BigInteger)
    created_at = Column(BigInteger)

    api_key = Column(String, nullable=True, unique=True)
    settings = Column(JSONField, nullable=True)
    info = Column(JSONField, nullable=True)

    oauth_sub = Column(Text, unique=True)


class UserSettings(BaseModel):
    ui: Optional[dict] = {}
    model_config = ConfigDict(extra="allow")


class UserModel(BaseModel):
    id: str
    name: str
    email: str
    role: str = "pending"
    profile_image_url: str

    last_active_at: int  # timestamp in epoch
    updated_at: int  # timestamp in epoch
    created_at: int  # timestamp in epoch

    api_key: Optional[str] = None
    settings: Optional[UserSettings] = None
    info: Optional[dict] = None

    oauth_sub: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


####################
# Forms
####################


class DAUForm(BaseModel):
    start_date: Optional[Union[str, date]] = (
        datetime.today() - relativedelta(days=7)
    ).date()
    end_date: Optional[Union[str, date]] = datetime.today().date()


class UserRoleUpdateForm(BaseModel):
    id: str
    role: str


class UserUpdateForm(BaseModel):
    name: str
    email: str
    profile_image_url: str
    password: Optional[str] = None


class UsersTable:
    async def insert_new_user(
        self,
        id: str,
        name: str,
        email: str,
        profile_image_url: str = "/user.png",
        role: str = "pending",
        oauth_sub: Optional[str] = None,
    ) -> Optional[UserModel]:
        async with get_db() as db:
            user = UserModel(
                **{
                    "id": id,
                    "name": name,
                    "email": email,
                    "role": role,
                    "profile_image_url": profile_image_url,
                    "last_active_at": int(time.time()),
                    "created_at": int(time.time()),
                    "updated_at": int(time.time()),
                    "oauth_sub": oauth_sub,
                }
            )
            result = User(**user.model_dump())
            db.add(result)
            await db.commit()
            if result:
                return user
            else:
                return None

    async def get_user_by_id(self, id: str) -> Optional[UserModel]:
        async with get_db() as db:
            user = await db.execute(select(User).where(User.id == id))
            user = user.scalar()
            if user:
                return UserModel.model_validate(user)

    async def get_user_by_api_key(self, api_key: str) -> Optional[UserModel]:
        async with get_db() as db:
            user = await db.execute(select(User).where(User.api_key == api_key))
            user = user.scalar()
            if user:
                return UserModel.model_validate(user)

    async def get_user_by_email(self, email: str) -> Optional[UserModel]:
        async with get_db() as db:
            user = await db.execute(select(User).where(User.email == email))
            user = user.scalar()
            if user:
                return UserModel.model_validate(user)

    async def get_user_by_oauth_sub(self, sub: str) -> Optional[UserModel]:
        async with get_db() as db:
            user = await db.execute(select(User).where(User.oauth_sub == sub))
            return UserModel.model_validate(user.scalar())

    async def get_users(self, skip: int = 0, limit: int = 50) -> List[UserModel]:
        async with get_db() as db:
            users = await db.execute(select(User))
            return [UserModel.model_validate(user) for user in users.scalars()]

    async def get_num_users(self) -> Optional[int]:
        async with get_db() as db:
            count = await db.execute(select(func.count(User.id)))
            return count.scalar()

    async def get_first_user(self) -> UserModel:
        async with get_db() as db:
            user = await db.execute(select(User).order_by(User.created_at))

            return UserModel.model_validate(user.scalar())

    async def update_user_role_by_id(self, id: str, role: str) -> Optional[UserModel]:
        async with get_db() as db:
            await db.execute(update(User).where(User.id == id).values(role=role))
            await db.commit()
            user = await db.get(User, id)
            return UserModel.model_validate(user)

    async def update_user_profile_image_url_by_id(
        self, id: str, profile_image_url: str
    ) -> Optional[UserModel]:
        async with get_db() as db:
            await db.execute(
                update(User)
                .where(User.id == id)
                .values(profile_image_url=profile_image_url)
            )
            await db.commit()

            user = db.query(User).filter_by(id=id).scalar()
            return UserModel.model_validate(user)

    async def update_user_last_active_by_id(self, id: str) -> Optional[UserModel]:
        async with get_db() as db:
            await db.execute(
                update(User)
                .where(User.id == id)
                .values(last_active_at=int(time.time()))
            )
            await db.commit()
            user = await db.get(User, id)
            return UserModel.model_validate(user)

    async def update_user_oauth_sub_by_id(
        self, id: str, oauth_sub: str
    ) -> Optional[UserModel]:
        async with get_db() as db:
            await db.execute(
                update(User).where(User.id == id).values(oauth_sub=oauth_sub)
            )
            await db.commit()

            user = await db.get(User, id)
            return UserModel.model_validate(user)

    async def update_user_by_id(self, id: str, updated: dict) -> Optional[UserModel]:
        async with get_db() as db:
            await db.execute(update(User).where(User.id == id).values(**updated))
            await db.commit()

            user = await db.get(User, id)
            return UserModel.model_validate(user)

    async def delete_user_by_id(self, id: str) -> bool:
        result = await Chats.delete_chats_by_user_id(id)

        if result:
            async with get_db() as db:
                # Delete User
                await db.execute(delete(User).where(User.id == id))
                await db.commit()

            return True

    async def update_user_api_key_by_id(self, id: str, api_key: str) -> bool:
        async with get_db() as db:
            await db.execute(update(User).where(User.id == id).values(api_key=api_key))
            await db.commit()
            return True

    async def get_user_api_key_by_id(self, id: str) -> Optional[str]:
        async with get_db() as db:
            user = await db.get(User, id)
            return user.api_key

    async def get_dau(self, form: DAUForm) -> List[UserModel]:
        async with get_db() as db:
            stmt = select(User).where(
                and_(
                    *[
                        User.last_active_at >= time.mktime(form.start_date.timetuple()),
                    ]
                )
            )
            users = await db.execute(stmt)
            users = users.scalars().all()
            return users


Users = UsersTable()
