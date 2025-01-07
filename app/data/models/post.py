from pydantic import BaseModel, Field
from datetime import datetime
from pathlib import Path


from ..utils import generate_uuid
from . import PyUUID


class Like(BaseModel):
    """
    Model for a single like to a comment or a post record.
    """
    id_user: PyUUID


class Dislike(Like):
    """
    Model for a single dislike to a comment or a post record.
    """
    id_user: PyUUID


class CommentHistory(BaseModel):
    """
    A Model for a single save of a comment history.
    """
    date: datetime
    content: str
    medias: list[str | Path] | None = None
    keys: list[str] | None = None
    nb_likes: int
    updated_by: PyUUID


class Comment(BaseModel):
    """
    Comment model for a single comment record.
    """
    uuid: PyUUID = Field(default_factory=generate_uuid)
    id_author: PyUUID
    date: datetime = Field(default_factory=datetime.now)
    content: str
    medias: list[str | Path] | None = None
    keys: list[str] | None = None
    likes: list[PyUUID] | None = None
    comments: list[PyUUID] | None = None
    history: list[CommentHistory] | None = None # or Field(default_factory=list)


class CommentRead(Comment):
    """
    Represent the public version of a comment record.
    """
    ...


class CommentCreate(Comment):
    """
    Comment model for a single creation of a comment record.
    """
    target: PyUUID
    uuid: PyUUID = Field(default_factory=generate_uuid)
    id_author: PyUUID
    date: datetime = Field(default_factory=datetime.now)
    content: str
    medias: list[str | Path] | None = None
    keys: list[str] | None = None
    likes: list[PyUUID] | None = None
    comments: list[PyUUID] | None = None


class CommentUpdate(BaseModel):
    """
    Comment model for updating a single comment record.
    """
    content: str
    medias: list[str | Path] | None = None
    keys: list[str] | None = None


class CommentCollection(BaseModel):
    """
    Comment model for a collection of comments.
    """
    comments: list[CommentRead]


class PostHistory(CommentHistory):
    """
    A Model for a single save of a post history.
    """
    title: str


class Post(Comment):
    """
    Post model for a single post record.
    """
    title: str
    history: list[PostHistory] | None = None


class PostRead(Post):
    """
    Represent the public version of a post record.
    """
    ...


class PostCreate(BaseModel):
    """
    Post model for a single creation of a post record.
    """
    uuid: PyUUID = Field(default_factory=generate_uuid)
    id_author: PyUUID | None = None
    date: datetime = Field(default_factory=datetime.now)
    title: str
    content: str
    medias: list[str | Path] | None = None
    keys: list[str] | None = None
    likes: list[PyUUID] | None = None
    comments: list[PyUUID] | None = None


class PostUpdate(CommentUpdate):
    """
    Post model for a single update to a post record.
    """
    title: str

class PostCollection(BaseModel):
    """
    Post model for a collection of posts.
    """
    posts: list[PostRead]
