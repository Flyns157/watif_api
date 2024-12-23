from pydantic import BaseModel, Field, UUID5
from ..utils import generate_uuid


class Thread(BaseModel):
    """
    A model for a thread.
    """
    id: str | UUID5 = Field(default_factory=generate_uuid)
    name: str
    public: bool = False
    id_owner: str | UUID5
    moderators: list[str |UUID5] | None = None
    members: list[str | UUID5] | None = None
    banned_users: list[str | UUID5] | None = None

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
    moderators: list[str | UUID5] | None = None
    members: list[str | UUID5] | None = None
    banned_users: list[str | UUID5] | None = None


class ThreadCollection(BaseModel):
    """
    A model for a collection of threads.
    """
    threads: list[ThreadRead]
