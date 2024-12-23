from pydantic import BaseModel
from .user import UserRead


class Token(BaseModel):
    access_token: str
    token_type: str
    user_info: UserRead


class TokenData(BaseModel):
    username: str | None = None
