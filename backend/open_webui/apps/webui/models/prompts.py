import time
from typing import List, Optional

from open_webui.apps.webui.internal.db import Base, get_db
from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Column, String, Text, delete, select, update

####################
# Prompts DB Schema
####################


class Prompt(Base):
    __tablename__ = "prompt"

    command = Column(String, primary_key=True)
    user_id = Column(String)
    title = Column(Text)
    content = Column(Text)
    timestamp = Column(BigInteger)


class PromptModel(BaseModel):
    command: str
    user_id: str
    title: str
    content: str
    timestamp: int  # timestamp in epoch

    model_config = ConfigDict(from_attributes=True)


####################
# Forms
####################


class PromptForm(BaseModel):
    command: str
    title: str
    content: str


class PromptsTable:
    async def insert_new_prompt(
        self, user_id: str, form_data: PromptForm
    ) -> Optional[PromptModel]:
        prompt = PromptModel(
            **{
                "user_id": user_id,
                "command": form_data.command,
                "title": form_data.title,
                "content": form_data.content,
                "timestamp": int(time.time()),
            }
        )
        async with get_db() as db:
            result = Prompt(**prompt.dict())
            db.add(result)
            await db.commit()
            await db.refresh(result)
            if result:
                return PromptModel.model_validate(result)

    async def get_prompt_by_command(self, command: str) -> Optional[PromptModel]:
        async with get_db() as db:
            prompt = await db.execute(select(Prompt).where(Prompt.command == command))
            prompt = prompt.scalar()
            if prompt:
                return PromptModel.model_validate(prompt)

    async def get_prompts(self) -> List[PromptModel]:
        async with get_db() as db:
            prompts = await db.execute(select(Prompt))
            return [PromptModel.model_validate(prompt) for prompt in prompts.scalars()]

    async def update_prompt_by_command(
        self, command: str, form_data: PromptForm
    ) -> Optional[PromptModel]:
        async with get_db() as db:
            prompt = await db.execute(
                update(Prompt)
                .where(Prompt.command == command)
                .values(
                    title=form_data.title,
                    content=form_data.content,
                    timestamp=int(time.time()),
                )
                .returning(Prompt)
            )

            await db.commit()
            prompt = prompt.scalar()
            return PromptModel.model_validate(prompt)

    async def delete_prompt_by_command(self, command: str) -> bool:
        async with get_db() as db:
            await db.execute(delete(Prompt).where(Prompt.command == command))
            await db.commit()
            return True


Prompts = PromptsTable()
