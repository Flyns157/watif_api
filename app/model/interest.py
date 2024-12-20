from pydantic import BaseModel, UUID5


class Interest(BaseModel):
    uuid: UUID5
    name: str
