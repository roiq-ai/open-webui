import logging
from typing import List, Optional

from open_webui.config import SRC_LOG_LEVELS
from open_webui.constants import ERROR_MESSAGES
from fastapi import APIRouter, Depends, HTTPException, Request, status
from open_webui.apps.webui.models.auths import Auths
from open_webui.apps.webui.models.chats import Chats
from open_webui.apps.webui.models.user_mapping import (
    UserMapping,
    UserMappingModel,
    UserMappingUpdateForm,
)
from open_webui.apps.webui.models.users import (
    UserModel,
    UserRoleUpdateForm,
    Users,
    UserSettings,
    UserUpdateForm,
    DAUForm,
)
from open_webui.utils.utils import get_admin_user, get_password_hash, get_verified_user
from pydantic import BaseModel
import pandas as pd
from fastapi_cache.decorator import cache

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])

router = APIRouter()

############################
# GetUsers
############################


@router.get("/", response_model=List[UserModel])
@cache(expire=60)
async def get_users(skip: int = 0, limit: int = 50, user=Depends(get_admin_user)):
    return await Users.get_users(skip, limit)


############################
# User Permissions
############################


@router.get("/permissions/user")
async def get_user_permissions(request: Request, user=Depends(get_admin_user)):
    return request.app.state.config.USER_PERMISSIONS


@router.post("/permissions/user")
async def update_user_permissions(
    request: Request, form_data: dict, user=Depends(get_admin_user)
):
    request.app.state.config.USER_PERMISSIONS = form_data
    return request.app.state.config.USER_PERMISSIONS


############################
# UpdateUserRole
############################


@router.post("/update/role", response_model=Optional[UserModel])
async def update_user_role(form_data: UserRoleUpdateForm, user=Depends(get_admin_user)):
    if user.id != form_data.id and form_data.id != Users.get_first_user().id:
        return await Users.update_user_role_by_id(form_data.id, form_data.role)

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=ERROR_MESSAGES.ACTION_PROHIBITED,
    )


############################
# GetUserSettingsBySessionUser
############################


@router.get("/user/settings", response_model=Optional[UserSettings])
async def get_user_settings_by_session_user(user=Depends(get_verified_user)):
    user = await Users.get_user_by_id(user.id)
    if user:
        return user.settings
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.USER_NOT_FOUND,
        )


############################
# UpdateUserSettingsBySessionUser
############################


@router.post("/user/settings/update", response_model=UserSettings)
async def update_user_settings_by_session_user(
    form_data: UserSettings, user=Depends(get_verified_user)
):
    user = await Users.update_user_by_id(user.id, {"settings": form_data.model_dump()})
    if user:
        return user.settings
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.USER_NOT_FOUND,
        )


############################
# GetUserInfoBySessionUser
############################


@router.get("/user/info", response_model=Optional[dict])
async def get_user_info_by_session_user(user=Depends(get_verified_user)):
    user = await Users.get_user_by_id(user.id)
    if user:
        return user.info
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.USER_NOT_FOUND,
        )


############################
# UpdateUserInfoBySessionUser
############################


@router.post("/user/info/update", response_model=Optional[dict])
async def update_user_info_by_session_user(
    form_data: dict, user=Depends(get_verified_user)
):
    user = await Users.get_user_by_id(user.id)
    if user:
        if user.info is None:
            user.info = {}

        user = await Users.update_user_by_id(
            user.id, {"info": {**user.info, **form_data}}
        )
        if user:
            return user.info
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.USER_NOT_FOUND,
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.USER_NOT_FOUND,
        )


############################
# GetUserById
############################


class UserResponse(BaseModel):
    name: str
    profile_image_url: str


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: str, user=Depends(get_verified_user)):
    # Check if user_id is a shared chat
    # If it is, get the user_id from the chat
    if user_id.startswith("shared-"):
        chat_id = user_id.replace("shared-", "")
        chat = await Chats.get_chat_by_id(chat_id)
        if chat:
            user_id = chat.user_id
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.USER_NOT_FOUND,
            )

    user = await Users.get_user_by_id(user_id)

    if user:
        return UserResponse(name=user.name, profile_image_url=user.profile_image_url)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.USER_NOT_FOUND,
        )


############################
# UpdateUserById
############################


@router.post("/{user_id}/update", response_model=Optional[UserModel])
async def update_user_by_id(
    user_id: str,
    form_data: UserUpdateForm,
    session_user=Depends(get_admin_user),
):
    user = await Users.get_user_by_id(user_id)

    if user:
        if form_data.email.lower() != user.email:
            email_user = await Users.get_user_by_email(form_data.email.lower())
            if email_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ERROR_MESSAGES.EMAIL_TAKEN,
                )

        if form_data.password:
            hashed = get_password_hash(form_data.password)
            log.debug(f"hashed: {hashed}")
            Auths.update_user_password_by_id(user_id, hashed)

        await Auths.update_email_by_id(user_id, form_data.email.lower())
        updated_user = await Users.update_user_by_id(
            user_id,
            {
                "name": form_data.name,
                "email": form_data.email.lower(),
                "profile_image_url": form_data.profile_image_url,
            },
        )

        if updated_user:
            return updated_user

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(),
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=ERROR_MESSAGES.USER_NOT_FOUND,
    )


############################
# DeleteUserById
############################


@router.delete("/{user_id}", response_model=bool)
async def delete_user_by_id(user_id: str, user=Depends(get_admin_user)):
    if user.id != user_id:
        result = await Auths.delete_auth_by_id(user_id)

        if result:
            return True

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_MESSAGES.DELETE_USER_ERROR,
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=ERROR_MESSAGES.ACTION_PROHIBITED,
    )


@router.post("/create/mapping", response_model=Optional[UserMappingModel])
async def update_user_mapping(
    form_data: UserMappingModel, user=Depends(get_admin_user)
):
    return await UserMapping.insert_new_user_mapping(user_mapping=form_data)


@router.post("/update/mapping/{username}", response_model=Optional[UserModel])
async def update_user_mapping(
    form_data: UserMappingUpdateForm, user=Depends(get_admin_user)
):
    return await UserMapping.update_user_mapping_table(form_data)


@router.post("/dau")
@cache(expire=60 * 60)
async def daily_active_users(form_data: DAUForm, user=Depends(get_admin_user)):
    form_data = DAUForm()
    users = pd.DataFrame.from_records(
        [
            {
                "email": x.email,
                "last_active_at": pd.Timestamp.utcfromtimestamp(
                    x.last_active_at
                ).strftime("%Y-%m-%d"),
            }
            for x in await Users.get_dau(form_data)
        ]
    )
    return (
        users.groupby("last_active_at").count().reset_index().to_dict(orient="records")
    )
