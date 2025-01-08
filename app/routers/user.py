from fastapi import (
    Body, 
    Depends, 
    Query, 
    HTTPException, 
    status, 
    APIRouter, 
    Response
)
from pymongo import ReturnDocument
from datetime import datetime
from pydantic import UUID5
from pathlib import Path

from ..data.models.user import (
    UserCreate,
    UserRead,
    UserUpdate,
    UserCollection,
    User,
)
from ..security.auth import (
    get_password_hash, 
    current_user_like, 
    current_user, 
    corresponds, 
    NOT_AUTHORIZED_ERROR, 
)
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
            permission="users:create:all"
        )
    )):
    """
    Insert a new user record with a hashed password.
    """
    user_dict = user.model_dump()
    user_dict["hashed_password"] = get_password_hash(user_dict.pop("password"))

    if "role" in user_dict:
        if not await mongodb.db.roles.find_one({"name": user_dict["role"]}):
            raise HTTPException(status_code=400, detail=f"Role '{user_dict['role']}' not found")
    else:
        user_dict["role"] = "user"

    try:
        from ..data.transactions.mongodb import User
        new_user = User(**user_dict)._save()

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
async def list_users(
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(100, description="Maximum number of records to return"),
    username: str = Query(None, description="Filter by username"),
    email: str = Query(None, description="Filter by email"),
    role: str = Query(None, description="Filter by role"),
):
    """
    List all of the users data in the database with pagination and filtering.
    """
    query = {}
    if username:
        query["username"] = {"$regex": username, "$options": "i"}
    if email:
        query["email"] = {"$regex": email, "$options": "i"}
    if role:
        query["role"] = role

    # TODO: Add sorting and filtering by other fields (e.g. birth_date, followers, etc.)

    # All fields that can be used for filtering:
    # role: str
    # username: str
    # email: EmailStr
    # name: str
    # surname: str
    # birth_date: Date
    # followed: list[PyUUID] | None
    # blocked: list[PyUUID] | None
    # interests: list[PyUUID] | None
    # disabled: bool = False

    users = await mongodb.db.users.find(query).skip(skip).limit(limit).to_list(limit)
    return UserCollection(users=users)


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
        current_user
    )):
    """
    Update individual fields of an existing user record.

    Only the provided fields will be updated.
    Any missing or `null` fields will be ignored.
    """
    if not (corresponds(uuid = uuid, permission = "users:update:own") or corresponds(current_user, permission="users:update:all")):
        raise NOT_AUTHORIZED_ERROR

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
        current_user
    )):
    """
    Remove a single user record from the database.
    """
    if not (corresponds(user=current_user, uuid=uuid, permission="users:delete:own") or corresponds(user=current_user, permission="users:delete:all")):
        raise NOT_AUTHORIZED_ERROR

    if (
        deleted_user := await mongodb.db.users.find_one({"uuid": str(uuid)})
    ) is not None:
        delete_result = await mongodb.db.users.delete_one({"uuid": str(uuid)})
        if delete_result.deleted_count == 1:
            return deleted_user

    raise HTTPException(status_code=404, detail=f"User {uuid} not found")


# TODO: Add a stat endpoint to get the stats of an user (like his number of likes, followers, etc.)
