import time
import uuid
from typing import List, Optional

from apps.webui.internal.db import Base, get_db
from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Column, String, Text, delete, select, update

####################
# Memory DB Schema
####################


class Memory(Base):
    __tablename__ = "memory"

    id = Column(String, primary_key=True)
    user_id = Column(String)
    content = Column(Text)
    updated_at = Column(BigInteger)
    created_at = Column(BigInteger)


class MemoryModel(BaseModel):
    id: str
    user_id: str
    content: str
    updated_at: int  # timestamp in epoch
    created_at: int  # timestamp in epoch

    model_config = ConfigDict(from_attributes=True)


####################
# Forms
####################


class MemoriesTable:
    async def insert_new_memory(
        self,
        user_id: str,
        content: str,
    ) -> Optional[MemoryModel]:
        with SessionLocal() as db:
            id = str(uuid.uuid4())

            memory = MemoryModel(
                **{
                    "id": id,
                    "user_id": user_id,
                    "content": content,
                    "created_at": int(time.time()),
                    "updated_at": int(time.time()),
                }
            )
            result = Memory(**memory.model_dump())
            db.add(result)
            await db.commit()
            await db.refresh(result)
            if result:
                return MemoryModel.model_validate(result)
            else:
                return None

    async def update_memory_by_id(
        self,
        id: str,
        content: str,
    ) -> Optional[MemoryModel]:
        async with get_db() as db:
            await db.execute(
                update(Memory)
                .where(Memory.id == id)
                .values(content=content, updated_at=int(time.time()))
            )
            await db.commit()
            return await self.get_memory_by_id(id)

    async def get_memories(self) -> Optional[List[MemoryModel]]:
        async with get_db() as db:
            memories = await db.execute(select(Memory))
            return [
                MemoryModel.model_validate(memory)
                for memory in memories.scalars().all()
            ]

    async def get_memories_by_user_id(
        self, user_id: str
    ) -> Optional[List[MemoryModel]]:
        async with get_db() as db:
            memories = await db.execute(select(Memory).where(Memory.user_id == user_id))

            return [
                MemoryModel.model_validate(memory)
                for memory in memories.scalars().all()
            ]

    async def get_memory_by_id(self, id: str) -> Optional[MemoryModel]:
        async with get_db() as db:
            memory = await db.get(Memory, id)
            return MemoryModel.model_validate(memory)

    async def delete_memory_by_id(self, id: str) -> bool:
        async with get_db() as db:
            await db.execute(delete(Memory).where(Memory.id == id))
            await db.commit()

            return True

    async def delete_memories_by_user_id(self, user_id: str) -> bool:
        async with get_db() as db:
            await db.execute(delete(Memory).where(Memory.user_id == user_id))
            await db.commit()

            return True

    async def delete_memory_by_id_and_user_id(self, id: str, user_id: str) -> bool:
        async with get_db() as db:
            await db.execute(
                delete(Memory).where(Memory.id == id, Memory.user_id == user_id)
            )
            await db.commit()

        return True


Memories = MemoriesTable()
