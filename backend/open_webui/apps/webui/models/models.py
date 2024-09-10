import logging
import time
from typing import List, Optional

from config import SRC_LOG_LEVELS
from open_webui.apps.webui.internal.db import Base, JSONField, get_db
from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Column, Text, delete, select, update

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])


####################
# Models DB Schema
####################


# ModelParams is a model for the data stored in the params field of the Model table
class ModelParams(BaseModel):
    model_config = ConfigDict(extra="allow")


# ModelMeta is a model for the data stored in the meta field of the Model table
class ModelMeta(BaseModel):
    profile_image_url: Optional[str] = "/static/favicon.png"

    description: Optional[str] = None
    """
        User-facing description of the model.
    """

    capabilities: Optional[dict] = None

    model_config = ConfigDict(extra="allow")


class Model(Base):
    __tablename__ = "model"

    id = Column(Text, primary_key=True)
    """
        The model's id as used in the API. If set to an existing model, it will override the model.
    """
    user_id = Column(Text)

    base_model_id = Column(Text, nullable=True)
    """
        An optional pointer to the actual model that should be used when proxying requests.
    """

    name = Column(Text)
    """
        The human-readable display name of the model.
    """

    params = Column(JSONField)
    """
        Holds a JSON encoded blob of parameters, see `ModelParams`.
    """

    meta = Column(JSONField)
    """
        Holds a JSON encoded blob of metadata, see `ModelMeta`.
    """

    updated_at = Column(BigInteger)
    created_at = Column(BigInteger)


class ModelModel(BaseModel):
    id: str
    user_id: str
    base_model_id: Optional[str] = None

    name: str
    params: ModelParams
    meta: ModelMeta

    updated_at: int  # timestamp in epoch
    created_at: int  # timestamp in epoch

    model_config = ConfigDict(from_attributes=True)


####################
# Forms
####################


class ModelResponse(BaseModel):
    id: str
    name: str
    meta: ModelMeta
    updated_at: int  # timestamp in epoch
    created_at: int  # timestamp in epoch


class ModelForm(BaseModel):
    id: str
    base_model_id: Optional[str] = None
    name: str
    meta: ModelMeta
    params: ModelParams


class ModelsTable:
    async def insert_new_model(
        self, form_data: ModelForm, user_id: str
    ) -> Optional[ModelModel]:
        model = ModelModel(
            **{
                **form_data.model_dump(),
                "user_id": user_id,
                "created_at": int(time.time()),
                "updated_at": int(time.time()),
            }
        )
        try:
            async with get_db() as db:
                result = Model(**model.model_dump())
                db.add(result)
                await db.commit()
                await db.refresh(result)

                if result:
                    return ModelModel.model_validate(result)
                else:
                    return None
        except Exception as e:
            print(e)
            return None

    async def get_all_models(self) -> List[ModelModel]:
        async with get_db() as db:
            models = await db.execute(select(Model))
            return [ModelModel.model_validate(model) for model in models.scalars()]

    async def get_model_by_id(self, id: str) -> Optional[ModelModel]:
        async with get_db() as db:
            model = await db.execute(select(Model).where(Model.id == id))
            model = model.scalar()
            if model:
                return ModelModel.model_validate(model)
            else:
                return None

    async def update_model_by_id(
        self, id: str, model: ModelForm
    ) -> Optional[ModelModel]:
        async with get_db() as db:
            # update only the fields that are present in the model
            result = await db.execute(
                update(Model)
                .where(Model.id == id)
                .values(
                    **{
                        k: v
                        for k, v in model.dict(exclude_unset=True).items()
                        if k != "id"
                    }
                )
                .returning(Model)
            )
            await db.commit()
            model = result.scalar()
            return ModelModel.model_validate(model)

    async def delete_model_by_id(self, id: str) -> bool:
        async with get_db() as db:
            await db.execute(delete(Model).where(Model.id == id))
            await db.commit()
            return True


Models = ModelsTable()
