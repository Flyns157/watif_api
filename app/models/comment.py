from pydantic import BaseModel, Field, UUID5
from datetime import datetime
from pathlib import Path


class Comment(BaseModel):
    """
    Comment model for a single comment record.
    """
    uuid: str | UUID5
    id_author: str | UUID5
    date: datetime = Field(default_factory=datetime.now)
    content: str
    medias: list[str | Path] | None = None
    keys: list[str | UUID5] | None = None
    likes: list[str |UUID5] | None = None
    comments: list[str |UUID5] | None = None
