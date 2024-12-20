from pydantic import BaseModel, EmailStr, UUID5, Field
from datetime import date, datetime
from pathlib import Path


class User(BaseModel):
    uuid: UUID5
    id_role: UUID5
    username: str
    hashed_password: str | bytes
    email: EmailStr
    name: str
    surname: str
    pp: Path = Path("default-avatar-icon-of-social-media-user-vector.jpg")
    birth_date: date
    followed: list[UUID5] | None
    blocked: list[UUID5] | None
    interests: list[UUID5] | None
    description: str = ""
    status: str = ""
    disabled: bool | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
