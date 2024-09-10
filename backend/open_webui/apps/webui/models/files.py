import logging
import time
from typing import List, Optional

from config import SRC_LOG_LEVELS
from open_webui.apps.webui.internal.db import Base, JSONField, get_db
from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Column, String, Text, delete, select

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])

####################
# Files DB Schema
####################


class File(Base):
    __tablename__ = "file"

    id = Column(String, primary_key=True)
    user_id = Column(String)
    filename = Column(Text)
    meta = Column(JSONField)
    created_at = Column(BigInteger)


class FileModel(BaseModel):
    id: str
    user_id: str
    filename: str
    meta: dict
    created_at: int  # timestamp in epoch

    model_config = ConfigDict(from_attributes=True)


####################
# Forms
####################


class FileModelResponse(BaseModel):
    id: str
    user_id: str
    filename: str
    meta: dict
    created_at: int  # timestamp in epoch


class FileForm(BaseModel):
    id: str
    filename: str
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


Files = FilesTable()
