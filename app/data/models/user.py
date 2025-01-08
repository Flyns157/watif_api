from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from pathlib import Path

from . import PyUUID, Date


class User(BaseModel):
    """
    Container for a single user record.
    """

    uuid: PyUUID
    role: str
    username: str
    hashed_password: str | bytes
    email: EmailStr
    name: str
    surname: str
    pp: str | Path = r"pp/default-avatar-icon-of-social-media-user-vector.jpg"
    birth_date: Date
    followed: list[PyUUID] | None
    blocked: list[PyUUID] | None
    interests: list[PyUUID] | None
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
                "pp": "pp/default-avatar-icon-of-social-media-user-vector.jpg",
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


class UserRead(BaseModel):
    """
    Container for a single user record returned by the API.
    """

    uuid: PyUUID
    role: str
    username: str
    email: EmailStr
    name: str
    surname: str
    pp: str | Path = r"pp/default-avatar-icon-of-social-media-user-vector.jpg"
    birth_date: Date
    followed: list[PyUUID] | None
    blocked: list[PyUUID] | None
    interests: list[PyUUID] | None
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
                "pp": "pp/default-avatar-icon-of-social-media-user-vector.jpg",
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


class UserCreate(BaseModel):
    """
    Container for a single user record used to create a new user.
    """

    uuid: PyUUID = None
    username: str
    password: str | bytes
    email: EmailStr
    name: str
    surname: str
    pp: str | Path = r"pp/default-avatar-icon-of-social-media-user-vector.jpg"
    birth_date: Date
    followed: list[PyUUID] | None = None
    blocked: list[PyUUID] | None = None
    interests: list[PyUUID] | None = None
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
                "pp": "pp/default-avatar-icon-of-social-media-user-vector.jpg",
                "birth_date": "1990-01-01",
                "followed": [],
                "blocked": [],
                "interests": [],
                "description": "I am a student at Example University."
            }
        },
    )


class UserUpdate(BaseModel):
    """
    Container for a single user record used to update an existing user.
    """

    role: str | None = None
    username: str | None = None
    password: str | bytes | None = None
    email: EmailStr | None = None
    name: str | None = None
    surname: str | None = None
    pp: Path | None = None
    birth_date: Date | None = None
    followed: list[PyUUID] | None = None
    blocked: list[PyUUID] | None = None
    interests: list[PyUUID] | None = None
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
                "pp": "pp/default-avatar-icon-of-social-media-user-vector.jpg",
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
    A container holding a list of `UserRead` instances.

    This exists because providing a top-level array in a JSON response can be a [vulnerability](https://haacked.com/archive/2009/06/25/json-hijacking.aspx/)
    """

    users: list[UserRead]
