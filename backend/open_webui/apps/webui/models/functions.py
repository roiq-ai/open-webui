import logging
import time
from typing import List, Optional

from config import SRC_LOG_LEVELS
from open_webui.apps.webui.internal.db import Base, JSONField, get_db
from open_webui.apps.webui.models.users import Users
from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Boolean, Column, String, Text, delete, select, update

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])

####################
# Functions DB Schema
####################


class Function(Base):
    __tablename__ = "function"

    id = Column(String, primary_key=True)
    user_id = Column(String)
    name = Column(Text)
    type = Column(Text)
    content = Column(Text)
    meta = Column(JSONField)
    valves = Column(JSONField)
    is_active = Column(Boolean)
    is_global = Column(Boolean)
    updated_at = Column(BigInteger)
    created_at = Column(BigInteger)


class FunctionMeta(BaseModel):
    description: Optional[str] = None
    manifest: Optional[dict] = {}


class FunctionModel(BaseModel):
    id: str
    user_id: str
    name: str
    type: str
    content: str
    meta: FunctionMeta
    is_active: bool = False
    is_global: bool = False
    updated_at: int  # timestamp in epoch
    created_at: int  # timestamp in epoch

    model_config = ConfigDict(from_attributes=True)


####################
# Forms
####################


class FunctionResponse(BaseModel):
    id: str
    user_id: str
    type: str
    name: str
    meta: FunctionMeta
    is_active: bool
    is_global: bool
    updated_at: int  # timestamp in epoch
    created_at: int  # timestamp in epoch


class FunctionForm(BaseModel):
    id: str
    name: str
    content: str
    meta: FunctionMeta


class FunctionValves(BaseModel):
    valves: Optional[dict] = None


class FunctionsTable:
    async def insert_new_function(
        self, user_id: str, type: str, form_data: FunctionForm
    ) -> Optional[FunctionModel]:
        function = FunctionModel(
            **{
                **form_data.model_dump(),
                "user_id": user_id,
                "type": type,
                "updated_at": int(time.time()),
                "created_at": int(time.time()),
            }
        )

        try:
            async with get_db() as db:
                result = Function(**function.model_dump())
                db.add(result)
                await db.commit()
                await db.refresh(result)
                if result:
                    return FunctionModel.model_validate(result)
                else:
                    return None
        except Exception as e:
            print(f"Error creating function: {e}")
            return None

    async def get_function_by_id(self, id: str) -> Optional[FunctionModel]:
        try:
            async with get_db() as db:
                function = await db.get(Function, id)
                return FunctionModel.model_validate(function)
        except:
            return None

    async def get_functions(self, active_only=False) -> List[FunctionModel]:
        async with get_db() as db:
            if active_only:
                funcs = await db.execute(
                    select(Function).where(Function.is_active == True)
                )
                return [
                    FunctionModel.model_validate(function)
                    for function in funcs.scalars()
                ]
            else:
                funcs = await db.execute(select(Function))
                return [
                    FunctionModel.model_validate(function)
                    for function in funcs.scalars()
                ]

    async def get_functions_by_type(
        self, type: str, active_only=False
    ) -> List[FunctionModel]:
        async with get_db() as db:
            if active_only:
                funcs = await db.execute(
                    select(Function).where(
                        Function.type == type, Function.is_active == True
                    )
                )
                return [
                    FunctionModel.model_validate(function)
                    for function in funcs.scalars()
                ]
            else:
                funcs = await db.execute(select(Function).where(Function.type == type))
                return [
                    FunctionModel.model_validate(function)
                    for function in funcs.scalars()
                ]

    async def get_global_filter_functions(self) -> List[FunctionModel]:
        async with get_db() as db:
            funcs = await db.execute(
                select(Function).where(
                    Function.type == "filter",
                    Function.is_active == True,
                    Function.is_global == True,
                )
            )
            return [
                FunctionModel.model_validate(function) for function in funcs.scalars()
            ]

    async def get_global_action_functions(self) -> List[FunctionModel]:
        async with get_db() as db:
            funcs = await db.execute(
                select(Function).where(
                    Function.type == "action",
                    Function.is_active == True,
                    Function.is_global == True,
                )
            )
            return [
                FunctionModel.model_validate(function) for function in funcs.scalars()
            ]

    async def get_function_valves_by_id(self, id: str) -> Optional[dict]:
        async with get_db() as db:
            function = await db.get(Function, id)
            return function.valves if function.valves else {}

    async def update_function_valves_by_id(
        self, id: str, valves: dict
    ) -> Optional[FunctionValves]:
        async with get_db() as db:
            await db.execute(
                update(Function)
                .where(Function.id == id)
                .values(
                    valves=valves,
                    updated_at=int(time.time()),
                )
                .returning(Function.id)
            )
            await db.commit()

    async def get_user_valves_by_id_and_user_id(
        self, id: str, user_id: str
    ) -> Optional[dict]:
        user = await Users.get_user_by_id(user_id)
        user_settings = user.settings.model_dump() if user.settings else {}

        # Check if user has "functions" and "valves" settings
        if "functions" not in user_settings:
            user_settings["functions"] = {}
        if "valves" not in user_settings["functions"]:
            user_settings["functions"]["valves"] = {}

        return user_settings["functions"]["valves"].get(id, {})

    async def update_user_valves_by_id_and_user_id(
        self, id: str, user_id: str, valves: dict
    ) -> Optional[dict]:
        try:
            user = await Users.get_user_by_id(user_id)
            user_settings = user.settings.model_dump() if user.settings else {}

            # Check if user has "functions" and "valves" settings
            if "functions" not in user_settings:
                user_settings["functions"] = {}
            if "valves" not in user_settings["functions"]:
                user_settings["functions"]["valves"] = {}

            user_settings["functions"]["valves"][id] = valves

            # Update the user settings in the database
            await Users.update_user_by_id(user_id, {"settings": user_settings})

            return user_settings["functions"]["valves"][id]
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    async def update_function_by_id(
        self, id: str, updated: dict
    ) -> Optional[FunctionModel]:
        async with get_db() as db:
            await db.execute(
                update(Function)
                .where(Function.id == id)
                .values(**{**updated, "updated_at": int(time.time())})
                .returning(Function.id)
            )
            await db.commit()
            return await self.get_function_by_id(id)

    async def deactivate_all_functions(self) -> Optional[bool]:
        async with get_db() as db:
            await db.execute(
                update(Function).values(
                    is_active=False,
                    updated_at=int(time.time()),
                )
            )
            return True

    async def delete_function_by_id(self, id: str) -> bool:
        async with get_db() as db:
            await db.execute(delete(Function).where(Function.id == id))
            await db.commit()

            return True


Functions = FunctionsTable()
