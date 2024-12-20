from pydantic import BaseModel, UUID5


class Key(BaseModel):
    uuid: UUID5
    name: str
