from pydantic import BaseModel, UUID5


class Interest(BaseModel):
    name: str
