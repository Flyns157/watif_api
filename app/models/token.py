from pydantic import BaseModel
from .user import GetUserModel


class Token(BaseModel):
    access_token: str
    token_type: str
    user_info: GetUserModel


class TokenData(BaseModel):
    username: str | None = None
