"""
The token models.
"""
from pydantic import BaseModel
from .user import UserRead
from . import PyUUID


class Token(BaseModel):
    """
    The token model.
    """
    access_token: str
    token_type: str
    user: UserRead


class TokenData(BaseModel):
    """
    The token data model.
    """
    uuid: PyUUID = None
