from fastapi import FastAPI, Body, HTTPException, status
from fastapi.staticfiles import StaticFiles

from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

from pydantic import ConfigDict, BaseModel, Field, EmailStr, UUID5
from pydantic.functional_validators import BeforeValidator

from typing_extensions import Annotated

from datetime import datetime, date, timedelta
from pymongo import ReturnDocument
from functools import wraps
import motor.motor_asyncio
from pathlib import Path
import uuid


# === Main application setup === #
app = FastAPI(
    title="Student Course API",
    summary="A sample application showing how to use FastAPI to add a ReST API to a MongoDB collection.",
)

# Mount the static files directory
app.mount("/storage", StaticFiles(directory="storage"), name="storage")

# @app.middleware("http") # TODO : Implement caching
# async def add_cache_control_header(request, call_next):
#     response = await call_next(request)
#     response.headers["Cache-Control"] = "no-store" 
#     return response

# Set up the password context for hashing and verifying passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # TODO : Implement OAuth2 authentication


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

DOMAIN_NAME = "localhost"

# Set up the MongoDB connection
client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
client.uuid_representation = 5
db = client.watif_test
user_collection = db.get_collection("users")

user_collection.create_index("uuid", unique=True)
user_collection.create_index("username", unique=True)
user_collection.create_index("email", unique=True)

# Represents an ObjectId field in the database.
# It will be represented as a `str` on the model so that it can be serialized to JSON.
PyObjectId = Annotated[str, BeforeValidator(str)]


# === Models for the API === #
class UserModel(BaseModel):
    """
    Container for a single user record.
    """

    uuid: str | UUID5
    id_role: str | UUID5 | None = None
    username: str
    hashed_password: str | bytes
    email: EmailStr
    name: str
    surname: str
    pp: str | Path = r"images/pp/default-avatar-icon-of-social-media-user-vector.jpg"
    birth_date: date
    followed: list[str | UUID5] | None
    blocked: list[str | UUID5] | None
    interests: list[str | UUID5] | None
    description: str = ""
    disabled: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "uuid": "ca990972-3410-50fd-8cc3-d32c1f2f2708",
                "username": "johndoe",
                "hashed_password": "pbkdf2:sha256:150000$v8v9v0$b1b2b3b4b5b6b7b8b9b0b1b2b3b4b5b6b7b8b9b0",
                "email": "johndoe@example.com",
                "name": "John",
                "surname": "Doe",
                "pp": "images/pp/default-avatar-icon-of-social-media-user-vector.jpg",
                "birth_date": "1990-01-01",
                "followed": [],
                "blocked": [],
                "interests": [],
                "description": "I am a student at Example University.",
                "disabled": False,
                "created_at": "2022-01-01T00:00:00.000Z",
                "updated_at": "2022-01-01T00:00:00.000Z"
            }
        },
    )


class GetUserModel(BaseModel):
    """
    Container for a single user record returned by the API.
    """

    uuid: str | UUID5
    id_role: str | UUID5 = None
    username: str
    email: EmailStr
    name: str
    surname: str
    pp: str | Path = r"images/pp/default-avatar-icon-of-social-media-user-vector.jpg"
    birth_date: date
    followed: list[str | UUID5] | None
    blocked: list[str | UUID5] | None
    interests: list[str | UUID5] | None
    description: str = ""
    disabled: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "uuid": "ca990972-3410-50fd-8cc3-d32c1f2f2708",
                "username": "johndoe",
                "email": "johndoe@example.com",
                "name": "John",
                "surname": "Doe",
                "pp": "images/pp/default-avatar-icon-of-social-media-user-vector.jpg",
                "birth_date": "1990-01-01",
                "followed": [],
                "blocked": [],
                "interests": [],
                "description": "I am a student at Example University.",
                "disabled": False,
                "created_at": "2022-01-01T00:00:00.000Z",
                "updated_at": "2022-01-01T00:00:00.000Z"
            }
        },
    )


class CreateUserModel(BaseModel):
    """
    Container for a single user record used to create a new user.
    """

    uuid: str | UUID5 = None
    username: str
    password: str | bytes
    email: EmailStr
    name: str
    surname: str
    pp: str | Path = r"images/pp/default-avatar-icon-of-social-media-user-vector.jpg"
    birth_date: date
    followed: list[str | UUID5] | None = None
    blocked: list[str | UUID5] | None = None
    interests: list[str | UUID5] | None = None
    description: str = ""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "uuid": "ca990972-3410-50fd-8cc3-d32c1f2f2708",
                "username": "johndoe",
                "password": "password123",
                "email": "johndoe@example.com",
                "name": "John",
                "surname": "Doe",
                "pp": "images/pp/default-avatar-icon-of-social-media-user-vector.jpg",
                "birth_date": "1990-01-01",
                "followed": [],
                "blocked": [],
                "interests": [],
                "description": "I am a student at Example University."
            }
        },
    )


class UpdateUserModel(BaseModel):
    """
    Container for a single user record used to update an existing user.
    """

    username: str | None = None
    password: str | bytes | None = None
    email: EmailStr | None = None
    name: str | None = None
    surname: str | None = None
    pp: Path | None = None
    birth_date: date | None = None
    followed: list[str | UUID5] | None = None
    blocked: list[str | UUID5] | None = None
    interests: list[str | UUID5] | None = None
    description: str | None = None

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "username": "johndoe",
                "password": "newpassword123",
                "email": "newjohndoe@example.com",
                "name": "John",
                "surname": "Doe",
                "pp": "images/pp/default-avatar-icon-of-social-media-user-vector.jpg",
                "birth_date": "1990-01-01",
                "followed": [],
                "blocked": [],
                "interests": [],
                "description": "I am a student at Example University."
            }
        },
    )


class UserCollection(BaseModel):
    """
    A container holding a list of `GetUserModel` instances.

    This exists because providing a top-level array in a JSON response can be a [vulnerability](https://haacked.com/archive/2009/06/25/json-hijacking.aspx/)
    """

    users: list[GetUserModel]


# === Verification functions === #
def validate_user_input(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        user = kwargs.get('user') or args[-1]
        if isinstance(user, CreateUserModel):
            # Check password strength
            if len(user.password) < 8:
                raise HTTPException(
                    status_code=400,
                    detail="Password must be at least 8 characters long"
                )
            
            # Check age (must be at least 13)
            if user.birth_date > datetime.now().date() - timedelta(days=13*365):
                raise HTTPException(
                    status_code=400,
                    detail="User must be at least 13 years old"
                )
            
            # Check if username/email exists
            existing_user = await user_collection.find_one({
                "$or": [
                    {"username": user.username},
                    {"email": user.email}
                ]
            })
            if existing_user:
                raise HTTPException(
                    status_code=400,
                    detail="Username or email already exists"
                )
        
        return await func(*args, **kwargs)
    return wrapper


# === Routes for the API === #
from fastapi import APIRouter

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
        user.uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, DOMAIN_NAME))

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


app.include_router(router)
