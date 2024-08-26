import json
import logging
import time
from typing import List, Optional

from apps.webui.internal.db import Base, get_db
from config import SRC_LOG_LEVELS
from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Column, String, Text, delete, select, update

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])

####################
# Documents DB Schema
####################


class Document(Base):
    __tablename__ = "document"

    collection_name = Column(String, primary_key=True)
    name = Column(String, unique=True)
    title = Column(Text)
    filename = Column(Text)
    content = Column(Text, nullable=True)
    user_id = Column(String)
    timestamp = Column(BigInteger)


class DocumentModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    collection_name: str
    name: str
    title: str
    filename: str
    content: Optional[str] = None
    user_id: str
    timestamp: int  # timestamp in epoch


####################
# Forms
####################


class DocumentResponse(BaseModel):
    collection_name: str
    name: str
    title: str
    filename: str
    content: Optional[dict] = None
    user_id: str
    timestamp: int  # timestamp in epoch


class DocumentUpdateForm(BaseModel):
    name: str
    title: str


class DocumentForm(DocumentUpdateForm):
    collection_name: str
    filename: str
    content: Optional[str] = None


class DocumentsTable:
    async def insert_new_doc(
        self, user_id: str, form_data: DocumentForm
    ) -> Optional[DocumentModel]:
        async with get_db() as db:
            document = DocumentModel(
                **{
                    **form_data.model_dump(),
                    "user_id": user_id,
                    "timestamp": int(time.time()),
                }
            )

            result = Document(**document.model_dump())
            db.add(result)
            db.commit()
            db.refresh(result)
            if result:
                return DocumentModel.model_validate(result)

    async def get_doc_by_name(self, name: str) -> Optional[DocumentModel]:
        async with get_db() as db:
            doc = await db.execute(select(Document).where(Document.name == name))

            document = doc.scalar()
            return DocumentModel.model_validate(document) if document else None

    async def get_docs(self) -> List[DocumentModel]:
        async with get_db() as db:
            docs = await db.execute(select(Document))

            return [DocumentModel.model_validate(doc) for doc in docs.scalars().all()]

    async def update_doc_by_name(
        self, name: str, form_data: DocumentUpdateForm
    ) -> Optional[DocumentModel]:
        async with get_db() as db:
            await db.execute(
                update(Document)
                .where(Document.name == name)
                .values(
                    title=form_data.title,
                    name=form_data.name,
                    timestamp=int(time.time),
                )
            )

            await db.commit()
            return await self.get_doc_by_name(form_data.name)

    async def update_doc_content_by_name(
        self, name: str, updated: dict
    ) -> Optional[DocumentModel]:
        doc = await self.get_doc_by_name(name)
        doc_content = json.loads(doc.content if doc.content else "{}")
        doc_content = {**doc_content, **updated}

        async with get_db() as db:
            await db.execute(
                update(Document)
                .where(Document.name == name)
                .values(
                    content=json.dumps(doc_content),
                    timestamp=int(time.time()),
                )
            )
            await db.commit()
            return await self.get_doc_by_name(name)

    async def delete_doc_by_name(self, name: str) -> bool:
        async with get_db() as db:
            await db.execute(delete(Document).where(Document.name == name))
            await db.commit()
            return True


Documents = DocumentsTable()
