import json
from typing import List, Optional

from open_webui.apps.webui.models.user_mapping import UserMappings
from open_webui.apps.webui.models.users import Users
from open_webui.constants import ERROR_MESSAGES
from fastapi import APIRouter, Depends, HTTPException, status
from open_webui.apps.webui.models.documents import (
    DocumentForm,
    DocumentResponse,
    Documents,
    DocumentUpdateForm,
)
from open_webui.utils.utils import get_admin_user, get_verified_user
from pydantic import BaseModel

router = APIRouter()


############################
# GetDocuments
############################


@router.get("/", response_model=List[DocumentResponse])
async def get_documents(user=Depends(get_verified_user)):
    mapped_user = await UserMappings.get_user_mapping_by_email(user.email)
    if mapped_user is None:
        return [
            DocumentResponse(
                **{
                    **doc.model_dump(),
                    "content": json.loads(doc.content if doc.content else "{}"),
                }
            )
            for doc in await Documents.get_documents_by_tag(user.id)
        ]
    docs = [
        DocumentResponse(
            **{
                **doc.model_dump(),
                "content": json.loads(doc.content if doc.content else "{}"),
            }
        )
        for doc in await Documents.get_documents_by_account(
            mapped_user.account_id, user.id
        )
    ]
    return docs


############################
# CreateNewDoc
############################


@router.post("/create", response_model=Optional[DocumentResponse])
async def create_new_doc(form_data: DocumentForm, user=Depends(get_admin_user)):
    doc = await Documents.get_doc_by_name(form_data.name)
    if doc is None:
        doc = await Documents.insert_new_doc(user.id, form_data)

        if doc:
            return DocumentResponse(
                **{
                    **doc.model_dump(),
                    "content": json.loads(doc.content if doc.content else "{}"),
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.FILE_EXISTS,
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.NAME_TAG_TAKEN,
        )


############################
# GetDocByName
############################


@router.get("/doc", response_model=Optional[DocumentResponse])
async def get_doc_by_name(name: str, user=Depends(get_verified_user)):
    doc = await Documents.get_doc_by_name(name)

    if doc:
        return DocumentResponse(
            **{
                **doc.model_dump(),
                "content": json.loads(doc.content if doc.content else "{}"),
            }
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )


############################
# TagDocByName
############################


class TagItem(BaseModel):
    name: str


class TagDocumentForm(BaseModel):
    name: str
    tags: List[dict]


@router.post("/doc/tags", response_model=Optional[DocumentResponse])
async def tag_doc_by_name(form_data: TagDocumentForm, user=Depends(get_verified_user)):
    doc = await Documents.update_doc_content_by_name(
        form_data.name, {"tags": form_data.tags}
    )

    if doc:
        return DocumentResponse(
            **{
                **doc.model_dump(),
                "content": json.loads(doc.content if doc.content else "{}"),
            }
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )


############################
# UpdateDocByName
############################


@router.post("/doc/update", response_model=Optional[DocumentResponse])
async def update_doc_by_name(
    name: str,
    form_data: DocumentUpdateForm,
    user=Depends(get_admin_user),
):
    doc = await Documents.update_doc_by_name(name, form_data)
    if doc:
        return DocumentResponse(
            **{
                **doc.model_dump(),
                "content": json.loads(doc.content if doc.content else "{}"),
            }
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.NAME_TAG_TAKEN,
        )


############################
# DeleteDocByName
############################


@router.delete("/doc/delete", response_model=bool)
async def delete_doc_by_name(name: str, user=Depends(get_admin_user)):
    result = await Documents.delete_doc_by_name(name)
    return result
