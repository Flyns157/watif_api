from pydantic import BaseModel, EmailStr
from bson import ObjectId
from datetime import datetime
from typing import List, Optional
from pathlib import Path

class UserDTO(BaseModel):
    id: str  # Utilisation d'une chaîne pour l'ID car ObjectId n'est pas directement JSON serializable
    role: str
    username: str
    email: EmailStr
    name: str
    surname: str
    pp: Optional[str] = None
    birthDate: str
    followed: List[str]
    blocked: List[str]
    interests: List[str]
    description: Optional[str] = ""
    status: Optional[str] = ""

    class Config:
        orm_mode = True
