from pydantic import BaseModel, EmailStr
from typing import List, Optional

class PrivateUserDTO(BaseModel):
    id: str  # Utilisation d'une chaîne pour l'ID car ObjectId n'est pas directement JSON serializable
    role: str
    username: str
    email: EmailStr
    name: str
    surname: str
    pp: Optional[str] = None
    birth_date: str
    followed: List[str]
    blocked: List[str]
    interests: List[str]
    description: Optional[str] = ""
    status: Optional[str] = ""

    class Config:
        orm_mode = True

class PublicUserDTO(BaseModel):
    id: str  # Utilisation d'une chaîne pour l'ID car ObjectId n'est pas directement JSON serializable
    role: str
    username: str
    pp: Optional[str] = None
    birth_date: str
    followed: List[str]
    interests: List[str]
    description: Optional[str] = ""
    status: Optional[str] = ""

    class Config:
        orm_mode = True
