from pydantic import BaseModel, EmailStr
from bson import str
from datetime import datetime
from typing import List, Optional
from pathlib import Path

class PostDTO(BaseModel):
    id: str
    id_thread: str
    id_author: str
    date: datetime
    title: str
    content: str
    medias: list[Path]
    keys: list[str]
    likes: list[str]
    comments: list[str]

    class Config:
        orm_mode = True
