from pydantic import BaseModel, Field, UUID5
from datetime import datetime
from pathlib import Path

from ..utils import generate_uuid


class CommentHistory(BaseModel):
    date: datetime
    content: str
    medias: list[str | Path] | None = None
    keys: list[str | UUID5] | None = None
    nb_likes: int


class CommentModel(BaseModel):
    """
    Comment model for a single comment record.
    """
    uuid: str | UUID5 = Field(default_factory=generate_uuid)
    id_author: str | UUID5
    date: datetime = Field(default_factory=datetime.now)
    content: str
    medias: list[str | Path] | None = None
    keys: list[str | UUID5] | None = None
    likes: list[str |UUID5] | None = None
    comments: list[str |UUID5] | None = None
    history: list[CommentHistory] | None = None


class CreateCommentModel(CommentModel):
    target: str | UUID5
    uuid: str | UUID5 = Field(default_factory=generate_uuid)
    id_author: str | UUID5
    date: datetime = Field(default_factory=datetime.now)
    content: str
    medias: list[str | Path] | None = None
    keys: list[str | UUID5] | None = None
    likes: list[str |UUID5] | None = None
    comments: list[str |UUID5] | None = None


class UpdateCommentModel(BaseModel):
    """
    Comment model for a single comment record.
    """
    content: str
    medias: list[str | Path] | None = None
    keys: list[str | UUID5] | None = None


class PostModel(CommentModel):
    title: str


class PostHistory(CommentHistory):
    title: str


class CreatePostModel(BaseModel):
    uuid: str | UUID5 = Field(default_factory=generate_uuid)
    id_author: str | UUID5
    date: datetime = Field(default_factory=datetime.now)
    title: str
    content: str
    medias: list[str | Path] | None = None
    keys: list[str | UUID5] | None = None
    likes: list[str |UUID5] | None = None
    comments: list[str |UUID5] | None = None


class UpdatePostModel(UpdateCommentModel):
    title: str
