from typing import Optional

from open_webui.apps.webui.internal.db import Base, get_db
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, Integer, String, select


class UserMapping(Base):
    __tablename__ = "username_mapping"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String)
    account_id = Column(String)
    email = Column(String)
    daterange = Column(String)
    account_name = Column(String)


class UserMappingModel(BaseModel):
    username: str
    account_id: str
    email: str
    daterange: str
    model_config = ConfigDict(from_attributes=True)


class UserMappingUpdateForm(BaseModel):
    username: Optional[str] = None
    account_id: Optional[str] = None
    email: Optional[str] = None
    daterange: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class UserMappingTable:
    async def insert_new_user_mapping(
        self, user_mapping: UserMappingModel
    ) -> UserMappingModel:
        async with get_db() as db:
            stmt = UserMapping.__table__.insert().values(
                username=user_mapping.username,
                account_id=user_mapping.account_id,
                email=user_mapping.email,
                daterange=user_mapping.daterange,
            )
            await db.execute(stmt)
            return user_mapping

    async def get_user_mapping_by_email(self, email: str) -> UserMappingModel:
        async with get_db() as db:
            stmt = select(UserMapping).where(UserMapping.email == email)
            result = await db.execute(stmt)
            records = result.scalar()
            return records

    async def update_user_mapping_table(self, form: UserMappingUpdateForm):
        with get_db() as db:
            stmt = (
                UserMapping.update()
                .where(UserMapping.email == form.email)
                .values(
                    username=form.username,
                    account_id=form.account_id,
                    daterange=form.daterange,
                )
            )
            await db.execute(stmt)
            await db.commit()
            return form


UserMappings = UserMappingTable()
