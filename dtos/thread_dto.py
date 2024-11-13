from pydantic import BaseModel

class ThreadDTO(BaseModel):
    id: str
    name: str
    id_owner: str
    admins: list[str]
    members: list[str]

    class Config:
        orm_mode = True
