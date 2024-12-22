from pydantic import BaseModel, UUID5


class Key(BaseModel):
    name: str
