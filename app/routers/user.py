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
from ..auth import get_password_hash, get_current_active_user, corresponds
from ..database.mongodb import user_collection, role_collection
from ..utils import generate_uuid


router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/",
    response_description="Add new user",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED
)
async def create_user(user: UserCreate = Body(...)):
    """
    Insert a new user record with a hashed password.
    """
    if user.uuid is None:
        user.uuid = str(generate_uuid())

    user_dict = user.model_dump()
    user_dict["hashed_password"] = get_password_hash(user_dict.pop("password"))
    user_dict["birth_date"] = user_dict["birth_date"].strftime("%Y-%m-%d")

    if "role_name" in user_dict:
        if not (role := await role_collection.find_one({"name": user_dict["role_name"]})):
            raise HTTPException(status_code=400, detail=f"Role '{user_dict['role_name']}' not found")
        # TODO: Check if the user has permission to create a user with the given role
        if user_dict["role_name"] != "user" and not corresponds(None, have_permission="create:admin"):
            raise HTTPException(status_code=403, detail="Not authorized to create an admin user")
    else:
        user_dict["role_name"] = "user"

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
    # TODO: Add pagination and filtering
    return UserCollection(users=await user_collection.find().to_list(1000))


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
        user := await user_collection.find_one({"uuid": str(uuid)})
    ) is not None:
        return user

    raise HTTPException(status_code=404, detail=f"User {uuid} not found")


@router.put(
    "/{uuid}",
    response_description="Update a user",
    response_model=UserRead,
)
async def update_user(uuid: UUID5, user: UserUpdate = Body(...), current_user: User = Depends(get_current_active_user)):
    """
    Update individual fields of an existing user record.

    Only the provided fields will be updated.
    Any missing or `null` fields will be ignored.
    """
    if not corresponds(current_user, be_user=uuid, have_permission="update:self") or not corresponds(current_user, have_permission="update:all"):
        raise HTTPException(status_code=403, detail="Not authorized to perform this action")

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
    response_model=UserRead,
)
async def delete_user(uuid: UUID5, current_user: User = Depends(get_current_active_user)):
    """
    Remove a single user record from the database.
    """
    if not corresponds(current_user, be_user=uuid, have_permission="delete:self") or not corresponds(current_user, have_permission="delete:all"):
        raise HTTPException(status_code=403, detail="Not authorized to perform this action")

    if (
        deleted_user := await user_collection.find_one({"uuid": str(uuid)})
    ) is not None:
        delete_result = await user_collection.delete_one({"uuid": str(uuid)})
        if delete_result.deleted_count == 1:
            return deleted_user

    raise HTTPException(status_code=404, detail=f"User {uuid} not found")


# TODO: Add a stat endpoint to get user stats
