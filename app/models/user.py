from pydantic import BaseModel, EmailStr, UUID5, Field, ConfigDict
from datetime import date, datetime
from fastapi import HTTPException
from functools import wraps
from pathlib import Path



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
        if isinstance(user, (CreateUserModel, UpdateUserModel)):
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
