from pydantic import BaseModel, Field
from bson import ObjectId

class Role(BaseModel):
    id: ObjectId = Field(None, alias='_id')
    name: str
    rights: list[str] | None
    extend: list[ObjectId] | None
