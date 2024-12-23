from pydantic import BaseModel
from .user import UserRead
from . import PyUUID


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserRead


class TokenData(BaseModel):
    uuid: PyUUID = None
