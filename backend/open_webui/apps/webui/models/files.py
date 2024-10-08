import logging
import time
from typing import List, Optional

from open_webui.config import SRC_LOG_LEVELS
from open_webui.apps.webui.internal.db import Base, JSONField, get_db
from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Column, String, Text, delete, select, update, JSON

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])


####################
# Files DB Schema
####################


class File(Base):
    __tablename__ = "file"

    id = Column(String, primary_key=True)
    user_id = Column(String)
    hash = Column(Text, nullable=True)

    filename = Column(Text)
    data = Column(JSON, nullable=True)
    meta = Column(JSONField)

    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)


class FileModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    hash: Optional[str] = None

    filename: str
    data: Optional[dict] = None
    meta: dict

    created_at: int  # timestamp in epoch
    updated_at: int  # timestamp in epoch


####################
# Forms
####################


class FileModelResponse(BaseModel):
    id: str
    user_id: str
    hash: Optional[str] = None

    filename: str
    data: Optional[dict] = None
    meta: dict

    created_at: int  # timestamp in epoch
    updated_at: int  # timestamp in epoch


class FileForm(BaseModel):
    id: str
    hash: Optional[str] = None
    filename: str
    data: dict = {}
    meta: dict = {}


class FilesTable:
    async def insert_new_file(
            self, user_id: str, form_data: FileForm
    ) -> Optional[FileModel]:
        async with get_db() as db:
            file = FileModel(
                **{
                    **form_data.model_dump(),
                    "user_id": user_id,
                    "created_at": int(time.time()),
                }
            )
            result = File(**file.model_dump())
            db.add(result)
            await db.commit()
            await db.refresh(result)
            if result:
                return FileModel.model_validate(result)

    async def get_file_by_id(self, id: str) -> Optional[FileModel]:
        async with get_db() as db:
            file = await db.get(File, id)
            if file is None:
                return None
            return FileModel.model_validate(file)

    async def get_files(self) -> List[FileModel]:
        async with get_db() as db:
            files = await db.execute(select(File))
            return [FileModel.model_validate(file) for file in files.scalars()]

    async def delete_file_by_id(self, id: str) -> bool:
        async with get_db() as db:
            await db.execute(delete(File).where(File.id == id))
            await db.commit()

            return True

    async def delete_all_files(self) -> bool:
        async with get_db() as db:
            await db.execute(delete(File))
            await db.commit()

            return True

    async def get_files_by_ids(self, ids):
        async with get_db() as db:
            files = await db.execute(select(File).where(File.id.in_(ids)))
            return [FileModel.model_validate(file) for file in files.scalars()]

    async def get_files_by_user_id(self, user_id: str) -> list[FileModel]:
        async with get_db() as db:
            stmt = select(File).where(File.user_id == user_id)
            res = await db.execute(stmt)
            return [
                FileModel.model_validate(file)
                for file in res.scalars().all()
            ]

    async def update_file_hash_by_id(self, id: str, hash: str) -> Optional[FileModel]:
        async with get_db() as db:
            stmt = update(File).where(File.id == id).values(hash=hash)
            await db.execute(stmt)
            await db.commit()
            file = await db.get(File, id)
            return FileModel.model_validate(file)

    async def update_file_data_by_id(self, id: str, data: dict) -> Optional[FileModel]:
        async with get_db() as db:
            stmt = update(File).where(File.id == id).values(data=data)
            await db.execute(stmt)
            await db.commit()
            file = await db.get(File, id)
            return FileModel.model_validate(file)

    async def update_file_metadata_by_id(self, id: str, meta: dict) -> Optional[FileModel]:
        async with get_db() as db:
            stmt = update(File).where(File.id == id).values(meta=meta)
            await db.execute(stmt)
            await db.commit()
            file = await db.get(File, id)
            return FileModel.model_validate(file)


Files = FilesTable()
