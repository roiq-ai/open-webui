import json
import time
import uuid
from typing import List, Optional

from open_webui.apps.webui.internal.db import Base, get_db
from pydantic import BaseModel, ConfigDict
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    String,
    Text,
    delete,
    select,
    update,
    and_,
)

####################
# Chat DB Schema
####################


class Chat(Base):
    __tablename__ = "chat"

    id = Column(String, primary_key=True)
    user_id = Column(String)
    title = Column(Text)
    chat = Column(Text)  # Save Chat JSON as Text

    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)

    share_id = Column(Text, unique=True, nullable=True)
    archived = Column(Boolean, default=False)


class ChatModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    title: str
    chat: str

    created_at: int  # timestamp in epoch
    updated_at: int  # timestamp in epoch

    share_id: Optional[str] = None
    archived: bool = False


####################
# Forms
####################


class ChatForm(BaseModel):
    chat: dict


class ChatTitleForm(BaseModel):
    title: str


class ChatResponse(BaseModel):
    id: str
    user_id: str
    title: str
    chat: dict
    updated_at: int  # timestamp in epoch
    created_at: int  # timestamp in epoch
    share_id: Optional[str] = None  # id of the chat to be shared
    archived: bool


class ChatTitleIdResponse(BaseModel):
    id: str
    title: str
    updated_at: int
    created_at: int


class ChatTable:
    async def insert_new_chat(
        self, user_id: str, form_data: ChatForm
    ) -> Optional[ChatModel]:
        async with get_db() as db:
            id = str(uuid.uuid4())
            chat = ChatModel(
                **{
                    "id": id,
                    "user_id": user_id,
                    "title": (
                        form_data.chat["title"]
                        if "title" in form_data.chat
                        else "New Chat"
                    ),
                    "chat": json.dumps(form_data.chat),
                    "created_at": int(time.time()),
                    "updated_at": int(time.time()),
                }
            )

            result = Chat(**chat.model_dump())
            db.add(result)
            await db.commit()
            await db.refresh(result)
            return ChatModel.model_validate(result) if result else None

    async def update_chat_by_id(self, id: str, chat: dict) -> Optional[ChatModel]:
        async with get_db() as db:
            chat_obj = await db.get(Chat, id)
            chat_obj.chat = json.dumps(chat)
            chat_obj.title = chat["title"] if "title" in chat else "New Chat"
            chat_obj.updated_at = int(time.time())
            await db.commit()
            await db.refresh(chat_obj)

            return ChatModel.model_validate(chat_obj)

    async def insert_shared_chat_by_chat_id(self, chat_id: str) -> Optional[ChatModel]:
        async with get_db() as db:
            # Get the existing chat to share
            chat = await db.get(Chat, chat_id)
            # Check if the chat is already shared
            if chat.share_id:
                return await self.get_chat_by_id_and_user_id(chat.share_id, "shared")
            # Create a new chat with the same data, but with a new ID
            shared_chat = ChatModel(
                **{
                    "id": str(uuid.uuid4()),
                    "user_id": f"shared-{chat_id}",
                    "title": chat.title,
                    "chat": chat.chat,
                    "created_at": chat.created_at,
                    "updated_at": int(time.time()),
                }
            )
            shared_result = Chat(**shared_chat.model_dump())
            db.add(shared_result)
            await db.commit()
            await db.refresh(shared_result)

            # Update the original chat with the share_id
            stmt = (
                update(Chat)
                .where(Chat.id == chat_id)
                .values(share_id=shared_chat.id)
                .returning(Chat.id)
            )
            result = await db.execute(stmt)
            await db.commit()
            result = result.fetchone()
            return shared_chat if (shared_result and result) else None

    async def update_shared_chat_by_chat_id(self, chat_id: str) -> Optional[ChatModel]:
        async with get_db() as db:
            print("update_shared_chat_by_id")
            chat = await db.get(Chat, chat_id)
            chat.title = chat.title
            chat.chat = chat.chat
            await db.commit()
            await db.refresh(chat)

            return await self.get_chat_by_id(chat.share_id)

    async def delete_shared_chat_by_chat_id(self, chat_id: str) -> bool:
        async with get_db() as db:
            await db.execute(delete(Chat).where(Chat.user_id == f"shared-{chat_id}"))
            await db.commit()

            return True

    async def update_chat_share_id_by_id(
        self, id: str, share_id: Optional[str]
    ) -> Optional[ChatModel]:
        async with get_db() as db:
            chat = await db.get(Chat, id)
            if not chat:
                return None

            chat.share_id = share_id
            await db.commit()
            await db.refresh(chat)
            return ChatModel.model_validate(chat)

    async def toggle_chat_archive_by_id(self, id: str) -> Optional[ChatModel]:
        async with get_db() as db:
            chat = await db.get(Chat, id)
            if not chat:
                return None
            chat.archived = not chat.archived
            await db.commit()
            await db.refresh(chat)
            return ChatModel.model_validate(chat)

    async def archive_all_chats_by_user_id(self, user_id: str) -> bool:
        async with get_db() as db:
            await db.execte(
                update(Chat).where(Chat.user_id == user_id).values(archived=True)
            )
            await db.commit()
            return True

    async def get_archived_chat_list_by_user_id(
        self, user_id: str, skip: int = 0, limit: int = 50
    ) -> List[ChatModel]:
        async with get_db() as db:
            all_chats = await db.execute(
                select(Chat)
                .where(Chat.user_id == user_id, Chat.archived == True)
                .order_by(Chat.updated_at.desc())
            )
            all_chats = all_chats.scalars()
            if not all_chats:
                return []
            return [ChatModel.model_validate(chat) for chat in all_chats]

    async def get_chat_list_by_user_id(
        self,
        user_id: str,
        include_archived: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> List[ChatModel]:
        async with get_db() as db:
            stmt = select(Chat).where(Chat.user_id == user_id)
            if not include_archived:
                stmt = stmt.where(Chat.archived == False)
            stmt = stmt.order_by(Chat.updated_at.desc())
            result = await db.execute(stmt)
            all_chats = result.scalars()
            if not all_chats:
                return []
            return [ChatModel.model_validate(chat) for chat in all_chats]

    async def get_chat_title_id_list_by_user_id(
        self,
        user_id: str,
        include_archived: bool = False,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> list[ChatTitleIdResponse]:
        async with get_db() as db:
            query = select(Chat).where(Chat.user_id == user_id)
            if not include_archived:
                query = query.where(Chat.archived == False)

            query = query.order_by(Chat.updated_at.desc())

            if limit:
                query = query.limit(limit)
            if skip:
                query = query.offset(skip)

            all_chats = await db.execute(query)

            # result has to be destrctured from sqlalchemy `row` and mapped to a dict since the `ChatModel`is not the returned dataclass.
            return [
                ChatTitleIdResponse.model_validate(
                    {
                        "id": chat.id,
                        "title": chat.title,
                        "updated_at": chat.updated_at,
                        "created_at": chat.created_at,
                    }
                )
                for chat in all_chats.scalars().all()
            ]

    async def get_chat_list_by_chat_ids(
        self, chat_ids: list[str], skip: int = 0, limit: int = 50
    ) -> list[ChatModel]:
        async with get_db() as db:
            all_chats = (
                select(Chat)
                .where(and_(Chat.id.in_(chat_ids), Chat.archived == False))
                .order_by(Chat.updated_at.desc())
            )
            resp = await db.execute(all_chats)
            if not resp.scalars():
                return []
            return [ChatModel.model_validate(chat) for chat in resp.scalars()]

    async def get_chat_by_id(self, id: str) -> Optional[ChatModel]:
        async with get_db() as db:
            chat = await db.get(Chat, id)
            if chat:
                return ChatModel.model_validate(chat)
            else:
                return None

    async def get_chat_by_share_id(self, id: str) -> Optional[ChatModel]:
        async with get_db() as db:
            chat = await db.execute(select(Chat).where(Chat.share_id == id))
            chat = chat.scalar()
            if chat:
                return await self.get_chat_by_id(id)
            else:
                return None

    async def get_chat_by_id_and_user_id(
        self, id: str, user_id: str
    ) -> Optional[ChatModel]:
        async with get_db() as db:
            chat = await db.execute(
                select(Chat).where(Chat.id == id, Chat.user_id == user_id)
            )
            chat = chat.scalar()
            if chat:
                return ChatModel.model_validate(chat)
            else:
                return None

    async def get_chats(self, skip: int = 0, limit: int = 50) -> List[ChatModel]:
        async with get_db() as db:
            chats = await db.execute(select(Chat).order_by(Chat.updated_at.desc()))
            all_chats = chats.scalars()
            if not all_chats:
                return []
            return [ChatModel.model_validate(chat) for chat in all_chats]

    async def get_chats_by_user_id(self, user_id: str) -> List[ChatModel]:
        async with get_db() as db:
            chats = await db.execute(
                select(Chat)
                .where(Chat.user_id == user_id)
                .order_by(Chat.updated_at.desc())
            )
            chats = chats.scalars()
            if not chats:
                return []
            return [ChatModel.model_validate(chat) for chat in chats.scalars()]

    async def get_archived_chats_by_user_id(self, user_id: str) -> List[ChatModel]:
        async with get_db() as db:
            chats = await db.exeute(
                select(Chat)
                .where(Chat.user_id == user_id, Chat.archived == True)
                .order_by(Chat.updated_at.desc())
            )
            return [ChatModel.model_validate(chat) for chat in chats.scalars()]

    async def delete_chat_by_id(self, id: str) -> bool:
        async with get_db() as db:
            await db.execute(delete(Chat).where(Chat.id == id))
            await db.commit()

            return True and await self.delete_shared_chat_by_chat_id(id)

    async def delete_chat_by_id_and_user_id(self, id: str, user_id: str) -> bool:
        async with get_db() as db:
            await db.execute(delete(Chat).where(Chat.id == id, Chat.user_id == user_id))
            await db.commit()

            return True and await self.delete_shared_chat_by_chat_id(id)

    async def delete_chats_by_user_id(self, user_id: str) -> bool:
        async with get_db() as db:
            await self.delete_shared_chats_by_user_id(user_id)
            await db.execute(delete(Chat).where(Chat.user_id == user_id))
            await db.commit()

            return True

    async def delete_shared_chats_by_user_id(self, user_id: str) -> bool:
        async with get_db() as db:
            chats_by_user = await db.execute(
                select(Chat).where(Chat.user_id == user_id)
            )
            chats_by_user = chats_by_user.scalars()
            shared_chat_ids = [f"shared-{chat.id}" for chat in chats_by_user]
            await db.execute(delete(Chat).where(Chat.user_id.in_(shared_chat_ids)))
            await db.commit()
            return True


Chats = ChatTable()
