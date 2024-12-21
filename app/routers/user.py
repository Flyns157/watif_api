from fastapi import Body, HTTPException, status, APIRouter
from pymongo import ReturnDocument
from datetime import datetime
from pydantic import UUID5
from pathlib import Path
import uuid

from ..models.user import (
    CreateUserModel,
    GetUserModel,
    UpdateUserModel,
    UserCollection,
)
from ..database.mongodb import user_collection
from ..auth import get_password_hash
from ..utils.config import Settings

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/",
    response_description="Add new user",
    response_model=GetUserModel,
    status_code=status.HTTP_201_CREATED
)
async def create_user(user: CreateUserModel = Body(...)):
    """
    Insert a new user record with a hashed password.
    """
    if user.uuid is None:
        user.uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, Settings.DOMAIN_NAME))

    user_dict = user.model_dump()
    user_dict["hashed_password"] = get_password_hash(user_dict.pop("password"))
    user_dict["birth_date"] = user_dict["birth_date"].strftime("%Y-%m-%d")

    try:
        new_user = await user_collection.insert_one(user_dict)
    except Exception as e:
        for field in ("username", "email", "uuid"):
            if field in user_dict and (user := await user_collection.find_one({field: user_dict[field]})) is not None:
                raise HTTPException(status_code=400, detail=f"A user with the {field} '{user_dict[field]}' already exists")

    created_user = await user_collection.find_one(
        {"uuid": user.uuid}
    )
    return created_user


@router.get(
    "/",
    response_description="List all users",
    response_model=UserCollection,
)
async def list_users():
    """
    List all of the users data in the database.

    The response is unpaginated and limited to 1000 results.
    """
    return UserCollection(users=await user_collection.find().to_list(1000))


@router.get(
    "/{uuid}",
    response_description="Get a single user",
    response_model=GetUserModel,
)
async def show_user(uuid: UUID5):
    """
    Get the record for a specific user, looked up by `uuid`.
    """
    if (
        user := await user_collection.find_one({"uuid": str(uuid)})
    ) is not None:
        return user

    raise HTTPException(status_code=404, detail=f"User {uuid} not found")


@router.put(
    "/{uuid}",
    response_description="Update a user",
    response_model=GetUserModel,
)
async def update_user(uuid: UUID5, user: UpdateUserModel = Body(...)):
    """
    Update individual fields of an existing student record.

    Only the provided fields will be updated.
    Any missing or `null` fields will be ignored.
    """
    user = {
        k: v for k, v in user.model_dump().items() if v is not None
    }

    if len(user) >= 1:
        user["updated_at"] = datetime.now()
        if "birth_date" in user:
            user["birth_date"] = user["birth_date"].strftime("%Y-%m-%d")
        if "pp" in user and isinstance(user["pp"], Path):
            user["pp"] = str(user["pp"])

        try:
            update_result = await user_collection.find_one_and_update(
                {"uuid": str(uuid)},
                {"$set": user},
                return_document=ReturnDocument.AFTER,
            )

            if update_result is None:
                raise HTTPException(status_code=404, detail=f"User {uuid} not found")
            return update_result

        except Exception as e:
            for field in ("username", "email"):
                if field in user and (user := await user_collection.find_one({field: user[field]})) is not None:
                    raise HTTPException(status_code=400, detail=f"A user with the {field} '{user[field]}' already exists")

    # The update is empty, but we should still return the matching document:
    if (existing_user := await user_collection.find_one({"uuid": str(uuid)})) is not None:
        return existing_user

    raise HTTPException(status_code=404, detail=f"User {uuid} not found")


@router.delete(
    "/{uuid}",
    response_description="Delete a user",
    response_model=GetUserModel,
)
async def delete_student(uuid: UUID5):
    """
    Remove a single student record from the database.
    """
    if (
        deleted_student := await user_collection.find_one({"uuid": str(uuid)})
    ) is not None:
        delete_result = await user_collection.delete_one({"uuid": str(uuid)})
        if delete_result.deleted_count == 1:
            return deleted_student

    raise HTTPException(status_code=404, detail=f"User {uuid} not found")
