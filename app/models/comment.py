from pydantic import BaseModel, Field, UUID5
from datetime import datetime
from pathlib import Path


class Comment(BaseModel):
    """
    Comment model for a single comment record.
    """
    uuid: UUID5
    id_author: UUID5
    date: datetime = Field(default_factory=datetime.now)
    content: str
    medias: list[Path] | None
    keys: list[UUID5] | None
    likes: list[UUID5] | None
    comments: list[UUID5] | None
