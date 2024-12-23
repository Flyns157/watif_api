from fastapi import Body, HTTPException, status, APIRouter, Depends
from pymongo import ReturnDocument
from datetime import datetime
from pydantic import UUID5
from pathlib import Path

from ..models.user import (
    UserCreate,
    UserRead,
    UserUpdate,
    UserCollection,
    User,
)
from ..auth import get_password_hash, current_user_like, current_user_likes, corresponds
from ..utils import generate_uuid
from .. import mongodb


router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/",
    response_description="Add new user",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED
)
async def create_user(
    user: UserCreate = Body(...),
    current_user: User = Depends(
        current_user_like(
            permission="create:all"
        )
    )):
    """
    Insert a new user record with a hashed password.
    """
    if user.uuid is None:
        user.uuid = str(generate_uuid())

    user_dict = user.model_dump()
    user_dict["hashed_password"] = get_password_hash(user_dict.pop("password"))

    if "role" in user_dict:
        if not await mongodb.db.roles.find_one({"name": user_dict["role"]}):
            raise HTTPException(status_code=400, detail=f"Role '{user_dict['role']}' not found")
    else:
        user_dict["role"] = "user"

    try:
        new_user = await mongodb.db.users.insert_one(user_dict)
    except Exception:
        for field in ("username", "email", "uuid"):
            if field in user_dict and (user := await mongodb.db.users.find_one({field: user_dict[field]})) is not None:
                raise HTTPException(status_code=400, detail=f"A user with the {field} '{user_dict[field]}' already exists")

    created_user = await mongodb.db.users.find_one(
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
    # TODO: Add pagination and filtering
    return UserCollection(users=await mongodb.db.users.find().to_list(1000))


@router.get(
    "/{uuid}",
    response_description="Get a single user",
    response_model=UserRead,
)
async def show_user(uuid: UUID5):
    """
    Get the record for a specific user, looked up by `uuid`.
    """
    if (
        user := await mongodb.db.users.find_one({"uuid": str(uuid)})
    ) is not None:
        return user

    raise HTTPException(status_code=404, detail=f"User {uuid} not found")


@router.put(
    "/{uuid}",
    response_description="Update a user",
    response_model=UserRead,
)
async def update_user(
    uuid: UUID5,
    user: UserUpdate = Body(...),
    current_user: User = Depends(
        lambda uuid: current_user_likes(
            {"uuid": uuid, "permission": "update:self"},
            {"permission": "update:all"},
        )
    )):
    """
    Update individual fields of an existing user record.

    Only the provided fields will be updated.
    Any missing or `null` fields will be ignored.
    """

    user = {
        k: v for k, v in user.model_dump().items() if v is not None
    }

    if len(user) >= 1:
        user["updated_at"] = datetime.now()

        if "pp" in user and isinstance(user["pp"], Path):
            user["pp"] = str(user["pp"])

        try:
            update_result = await mongodb.db.users.find_one_and_update(
                {"uuid": str(uuid)},
                {"$set": user},
                return_document=ReturnDocument.AFTER,
            )

            if update_result is None:
                raise HTTPException(status_code=404, detail=f"User {uuid} not found")
            return update_result

        except Exception:
            for field in ("username", "email"):
                if field in user and (user := await mongodb.db.users.find_one({field: user[field]})) is not None:
                    raise HTTPException(status_code=400, detail=f"A user with the {field} '{user[field]}' already exists")

    # The update is empty, but we should still return the matching document:
    if (existing_user := await mongodb.db.users.find_one({"uuid": str(uuid)})) is not None:
        return existing_user

    raise HTTPException(status_code=404, detail=f"User {uuid} not found")


@router.delete(
    "/{uuid}",
    response_description="Delete a user",
    response_model=UserRead,
)
async def delete_user(
    uuid: UUID5,
    current_user: User = Depends(
        current_user_likes(
            {"uuid": Depends(), "permission":"delete:self"},
            {"permission": "delete:all"},
        )
    )):
    """
    Remove a single user record from the database.
    """
    if not corresponds(current_user, be_user=uuid, have_permission="delete:self") or not corresponds(current_user, have_permission="delete:all"):
        raise HTTPException(status_code=403, detail="Not authorized to perform this action")

    if (
        deleted_user := await mongodb.db.users.find_one({"uuid": str(uuid)})
    ) is not None:
        delete_result = await mongodb.db.users.delete_one({"uuid": str(uuid)})
        if delete_result.deleted_count == 1:
            return deleted_user

    raise HTTPException(status_code=404, detail=f"User {uuid} not found")


# TODO: Add a stat endpoint to get user stats
