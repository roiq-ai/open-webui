import logging
import time
from typing import List, Optional

from config import SRC_LOG_LEVELS
from open_webui.apps.webui.internal.db import Base, JSONField, get_db
from open_webui.apps.webui.models.users import Users
from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Column, String, Text, delete, select, update

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])

####################
# Tools DB Schema
####################


class Tool(Base):
    __tablename__ = "tool"

    id = Column(String, primary_key=True)
    user_id = Column(String)
    name = Column(Text)
    content = Column(Text)
    specs = Column(JSONField)
    meta = Column(JSONField)
    valves = Column(JSONField)
    updated_at = Column(BigInteger)
    created_at = Column(BigInteger)


class ToolMeta(BaseModel):
    description: Optional[str] = None
    manifest: Optional[dict] = {}


class ToolModel(BaseModel):
    id: str
    user_id: str
    name: str
    content: str
    specs: List[dict]
    meta: ToolMeta
    updated_at: int  # timestamp in epoch
    created_at: int  # timestamp in epoch

    model_config = ConfigDict(from_attributes=True)


####################
# Forms
####################


class ToolResponse(BaseModel):
    id: str
    user_id: str
    name: str
    meta: ToolMeta
    updated_at: int  # timestamp in epoch
    created_at: int  # timestamp in epoch


class ToolForm(BaseModel):
    id: str
    name: str
    content: str
    meta: ToolMeta


class ToolValves(BaseModel):
    valves: Optional[dict] = None


class ToolsTable:
    async def insert_new_tool(
        self, user_id: str, form_data: ToolForm, specs: List[dict]
    ) -> Optional[ToolModel]:
        async with get_db() as db:
            tool = ToolModel(
                **{
                    **form_data.model_dump(),
                    "specs": specs,
                    "user_id": user_id,
                    "updated_at": int(time.time()),
                    "created_at": int(time.time()),
                }
            )

            result = Tool(**tool.model_dump())
            db.add(result)
            await db.commit()
            await db.refresh(result)
            if result:
                return ToolModel.model_validate(result)

    async def get_tool_by_id(self, id: str) -> Optional[ToolModel]:
        async with get_db() as db:
            tool = await db.get(Tool, id)
            if tool:
                return ToolModel.model_validate(tool)

    async def get_tools(self) -> List[ToolModel]:
        async with get_db() as db:
            tools = await db.execute(select(Tool))
            return [ToolModel.model_validate(tool) for tool in tools.scalars()]

    async def get_tool_valves_by_id(self, id: str) -> Optional[dict]:
        async with get_db() as db:
            tool = await db.get(Tool, id)
            if tool:
                return tool.valves if tool.valves else {}

    async def update_tool_valves_by_id(
        self, id: str, valves: dict
    ) -> Optional[ToolValves]:
        async with get_db() as db:
            await db.execute(update(Tool).where(Tool.id == id).values(valves=valves))
            await db.commit()
            return await self.get_tool_by_id(id)

    async def get_user_valves_by_id_and_user_id(
        self, id: str, user_id: str
    ) -> Optional[dict]:
        user = await Users.get_user_by_id(user_id)
        if not user:
            return None
        user_settings = user.settings.model_dump() if user.settings else {}

        # Check if user has "tools" and "valves" settings
        if "tools" not in user_settings:
            user_settings["tools"] = {}
        if "valves" not in user_settings["tools"]:
            user_settings["tools"]["valves"] = {}

        return user_settings["tools"]["valves"].get(id, {})

    async def update_user_valves_by_id_and_user_id(
        self, id: str, user_id: str, valves: dict
    ) -> Optional[dict]:
        user = await Users.get_user_by_id(user_id)
        if not user:
            return None
        user_settings = user.settings.model_dump() if user.settings else {}

        # Check if user has "tools" and "valves" settings
        if "tools" not in user_settings:
            user_settings["tools"] = {}
        if "valves" not in user_settings["tools"]:
            user_settings["tools"]["valves"] = {}

        user_settings["tools"]["valves"][id] = valves

        # Update the user settings in the database
        await Users.update_user_by_id(user_id, {"settings": user_settings})

        return user_settings["tools"]["valves"][id]

    async def update_tool_by_id(self, id: str, updated: dict) -> Optional[ToolModel]:
        async with get_db() as db:
            await db.execute(
                update(Tool)
                .where(Tool.id == id)
                .values(**updated, updated_at=int(time.time()))
            )
            await db.commit()

            tool = await db.get(Tool, id)
            await db.refresh(tool)
            return ToolModel.model_validate(tool)

    async def delete_tool_by_id(self, id: str) -> bool:
        async with get_db() as db:
            await db.execute(delete(Tool).where(Tool.id == id))
            await db.commit()

            return True


Tools = ToolsTable()
