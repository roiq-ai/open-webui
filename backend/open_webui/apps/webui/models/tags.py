import logging
import time
import uuid
from typing import List, Optional

from open_webui.config import SRC_LOG_LEVELS
from open_webui.apps.webui.internal.db import Base, get_db
from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Column, String, Text, delete, func, select


log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])

####################
# Tag DB Schema
####################


class Tag(Base):
    __tablename__ = "tag"

    id = Column(String, primary_key=True)
    name = Column(String)
    user_id = Column(String)
    data = Column(Text, nullable=True)


class ChatIdTag(Base):
    __tablename__ = "chatidtag"

    id = Column(String, primary_key=True)
    tag_name = Column(String)
    chat_id = Column(String)
    user_id = Column(String)
    timestamp = Column(BigInteger)


class TagModel(BaseModel):
    id: str
    name: str
    user_id: str
    data: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ChatIdTagModel(BaseModel):
    id: str
    tag_name: str
    chat_id: str
    user_id: str
    timestamp: int

    model_config = ConfigDict(from_attributes=True)


####################
# Forms
####################


class ChatIdTagForm(BaseModel):
    tag_name: str
    chat_id: str


class TagChatIdsResponse(BaseModel):
    chat_ids: List[str]


class ChatTagsResponse(BaseModel):
    tags: List[str]


class TagTable:
    async def insert_new_tag(self, name: str, user_id: str) -> Optional[TagModel]:
        async with get_db() as db:
            id = str(uuid.uuid4())
            tag = TagModel(**{"id": id, "user_id": user_id, "name": name})
            result = Tag(**tag.model_dump())
            db.add(result)
            await db.commit()
            await db.refresh(result)
            if result:
                return TagModel.model_validate(result)
            else:
                return None

    async def get_tag_by_name_and_user_id(
        self, name: str, user_id: str
    ) -> Optional[TagModel]:
        async with get_db() as db:
            tag = await db.execute(
                select(Tag).where(Tag.name == name, Tag.user_id == user_id)
            )
            return TagModel.model_validate(tag.scalar())

    async def add_tag_to_chat(
        self, user_id: str, form_data: ChatIdTagForm
    ) -> Optional[ChatIdTagModel]:
        tag = await self.get_tag_by_name_and_user_id(form_data.tag_name, user_id)
        if tag is None:
            tag = await self.insert_new_tag(form_data.tag_name, user_id)

        id = str(uuid.uuid4())
        chatIdTag = ChatIdTagModel(
            **{
                "id": id,
                "user_id": user_id,
                "chat_id": form_data.chat_id,
                "tag_name": tag.name,
                "timestamp": int(time.time()),
            }
        )
        async with get_db() as db:
            result = ChatIdTag(**chatIdTag.model_dump())
            db.add(result)
            await db.commit()
            await db.refresh(result)
            if result:
                return ChatIdTagModel.model_validate(result)
            else:
                return None

    async def get_tags_by_user_id(self, user_id: str) -> List[TagModel]:
        async with get_db() as db:
            tags = await db.execute(
                select(Tag).where(Tag.user_id == user_id).order_by(Tag.name.desc())
            )

            tag_names = [chat_id_tag.tag_name for chat_id_tag in tags.scalars()]
            tag_names = await db.execute(select(Tag).where(Tag.name.in_(tag_names)))
            return [TagModel.model_validate(tag) for tag in tag_names.scalars()]

    async def get_tags_by_chat_id_and_user_id(
        self, chat_id: str, user_id: str
    ) -> List[TagModel]:
        async with get_db() as db:
            tag_names = await db.execute(
                select(ChatIdTag.tag_name)
                .where(ChatIdTag.chat_id == chat_id, ChatIdTag.user_id == user_id)
                .order_by(ChatIdTag.timestamp.desc())
            )
            tag_names = [x for x in tag_names.scalars()]
            tags = await db.execute(select(Tag).where(Tag.name.in_(tag_names)))
            return [TagModel.model_validate(tag) for tag in tags.scalars()]

    async def get_chat_ids_by_tag_name_and_user_id(
        self, tag_name: str, user_id: str
    ) -> List[ChatIdTagModel]:
        async with get_db() as db:
            tags = await db.execute(
                select(ChatIdTag)
                .where(ChatIdTag.tag_name == tag_name, ChatIdTag.user_id == user_id)
                .order_by(ChatIdTag.timestamp.desc())
            )
            return [
                ChatIdTagModel.model_validate(chat_id_tag)
                for chat_id_tag in tags.scalars()
            ]

    async def count_chat_ids_by_tag_name_and_user_id(
        self, tag_name: str, user_id: str
    ) -> int:
        async with get_db() as db:
            counts = await db.execute(
                select(func.count(ChatIdTag.id)).where(
                    ChatIdTag.tag_name == tag_name, ChatIdTag.user_id == user_id
                )
            )
            return counts.scalar()

    async def delete_tag_by_tag_name_and_user_id(
        self, tag_name: str, user_id: str
    ) -> bool:
        async with get_db() as db:
            await db.execute(
                delete(Tag).where(Tag.name == tag_name, Tag.user_id == user_id)
            )
            await db.commit()

            tag_count = await self.count_chat_ids_by_tag_name_and_user_id(
                tag_name, user_id
            )
            if tag_count == 0:
                # Remove tag item from Tag col as well
                await db.execute(
                    delete(Tag).where(Tag.name == tag_name, Tag.user_id == user_id)
                )
                await db.commit()
            return True

    async def delete_tag_by_tag_name_and_chat_id_and_user_id(
        self, tag_name: str, chat_id: str, user_id: str
    ) -> bool:
        async with get_db() as db:
            await db.execute(
                delete(ChatIdTag).where(
                    ChatIdTag.tag_name == tag_name,
                    ChatIdTag.chat_id == chat_id,
                    ChatIdTag.user_id == user_id,
                )
            )
            await db.commit()

            tag_count = await self.count_chat_ids_by_tag_name_and_user_id(
                tag_name, user_id
            )
            if tag_count == 0:
                # Remove tag item from Tag col as well
                await db.execute(
                    delete(Tag).where(Tag.name == tag_name, Tag.user_id == user_id)
                )
                await db.commit()

            return True

    async def delete_tags_by_chat_id_and_user_id(
        self, chat_id: str, user_id: str
    ) -> bool:
        tags = await self.get_tags_by_chat_id_and_user_id(chat_id, user_id)

        for tag in tags:
            await self.delete_tag_by_tag_name_and_chat_id_and_user_id(
                tag.tag_name, chat_id, user_id
            )

        return True


Tags = TagTable()
