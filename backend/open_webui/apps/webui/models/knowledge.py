import logging
import time
from typing import Optional
import uuid

from open_webui.apps.webui.internal.db import Base, get_db
from open_webui.env import SRC_LOG_LEVELS
from pydantic import BaseModel, ConfigDict
from sqlalchemy import (
    BigInteger,
    Column,
    Text,
    JSON,
    select,
    delete,
    update,
)


log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])

####################
# Knowledge DB Schema
####################


class Knowledge(Base):
    __tablename__ = "knowledge"

    id = Column(Text, unique=True, primary_key=True)
    user_id = Column(Text)

    name = Column(Text)
    description = Column(Text)

    data = Column(JSON, nullable=True)
    meta = Column(JSON, nullable=True)

    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)


class KnowledgeModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str

    name: str
    description: str

    data: Optional[dict] = None
    meta: Optional[dict] = None

    created_at: int  # timestamp in epoch
    updated_at: int  # timestamp in epoch


####################
# Forms
####################


class KnowledgeResponse(BaseModel):
    id: str
    name: str
    description: str
    data: Optional[dict] = None
    meta: Optional[dict] = None
    created_at: int  # timestamp in epoch
    updated_at: int  # timestamp in epoch


class KnowledgeForm(BaseModel):
    name: str
    description: str
    data: Optional[dict] = None


class KnowledgeUpdateForm(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    data: Optional[dict] = None


class KnowledgeTable:
    async def insert_new_knowledge(
        self, user_id: str, form_data: KnowledgeForm
    ) -> Optional[KnowledgeModel]:
        async with get_db() as db:
            knowledge = KnowledgeModel(
                **{
                    **form_data.model_dump(),
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "created_at": int(time.time()),
                    "updated_at": int(time.time()),
                }
            )
            result = Knowledge(**knowledge.model_dump())
            db.add(result)
            await db.commit()
            await db.refresh(result)
            if result:
                return KnowledgeModel.model_validate(result)
            else:
                return None

    async def get_knowledge_items(self) -> list[KnowledgeModel]:
        async with get_db() as db:
            stmt = select(Knowledge).order_by(Knowledge.updated_at.desc())
            res = await db.execute(stmt)
            return [
                KnowledgeModel.model_validate(knowledge)
                for knowledge in res.scalars().all()
            ]

    async def get_knowledge_by_id(self, id: str) -> Optional[KnowledgeModel]:
        async with get_db() as db:
            stmt = select(Knowledge).where(Knowledge.id == id)
            res = await db.execute(stmt)
            res = res.scalar()
            return KnowledgeModel.model_validate(res) if res else None

    async def update_knowledge_by_id(
        self, id: str, form_data: KnowledgeUpdateForm, overwrite: bool = False
    ) -> Optional[KnowledgeModel]:
        try:
            async with get_db() as db:
                stmt = (
                    update(Knowledge)
                    .where(Knowledge.id == id)
                    .values(
                        {
                            **form_data.model_dump(exclude_none=True),
                            "updated_at": int(time.time()),
                        }
                    )
                )
                await db.execute(stmt)
                await db.commit()
                return await self.get_knowledge_by_id(id=id)
        except Exception as e:
            log.exception(e)
            return None

    async def delete_knowledge_by_id(self, id: str) -> bool:
        try:
            async with get_db() as db:
                query = delete(Knowledge).where(Knowledge.id == id)
                await db.execute(query)
                await db.commit()
                return True
        except Exception:
            return False


Knowledges = KnowledgeTable()
