from pydantic import BaseModel, Field, UUID5
from ..utils import generate_uuid


class Thread(BaseModel):
    id: str | UUID5 = Field(default_factory=generate_uuid)
    name: str
    public: bool
    id_owner: str | UUID5
    moderators: list[str |UUID5] | None = None
    members: list[str | UUID5] | None = None
