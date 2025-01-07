from pydantic import BaseModel, Field

from ..utils import generate_uuid
from . import PyUUID

class Thread(BaseModel):
    """
    A model for a thread.
    """
    uuid: PyUUID = Field(default_factory=generate_uuid)
    name: str
    public: bool = False
    id_owner: PyUUID | None = None
    moderators: list[PyUUID] | None = None
    members: list[PyUUID] | None = None
    banned_users: list[PyUUID] | None = None

class ThreadRead(Thread):
    """
    A model for reading a thread.
    """
    ...


class ThreadCreate(Thread):
    """
    A model for creating a thread.
    """
    ...


class ThreadUpdate(BaseModel):
    """
    A model for updating a thread.
    """
    name: str | None = None
    public: bool | None = None
    moderators: list[PyUUID] | None = None
    members: list[PyUUID] | None = None
    banned_users: list[PyUUID] | None = None


class ThreadCollection(BaseModel):
    """
    A model for a collection of threads.
    """
    threads: list[ThreadRead]
