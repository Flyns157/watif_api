from pydantic import BaseModel, Field, UUID5


class Thread(BaseModel):
    id: UUID5 = Field(default_factory=UUID5)
    name: str
    public: bool
    id_owner: UUID5
    moderators: list[UUID5] | None
    members: list[UUID5] | None
