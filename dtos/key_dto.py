from pydantic import BaseModel, EmailStr
from bson import ObjectId
from datetime import datetime
from typing import List, Optional
from pathlib import Path

class KeyDTO(BaseModel):
    _id: str
    name: str

    class Config:
        orm_mode = True
