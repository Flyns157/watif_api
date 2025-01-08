"""
Key models.
"""
from pydantic import BaseModel


class Key(BaseModel):
    """
    A key model.
    """
    name: str

class KeyRead(Key):
    """
    A public key model.
    """
    ...

class KeyCreate(Key):
    """
    A key creation model.
    """

class KeyCollection(BaseModel):
    """
    A collection of keys.
    """
    keys: list[KeyRead] = []
