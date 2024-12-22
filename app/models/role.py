from pydantic import BaseModel

class Role(BaseModel):
    name: str
    rights: list[str] | None
    inherits: list[str] | None = None
