from dataclasses import dataclass, field
from typing import Generator
from bson import ObjectId
from datetime import datetime
from pathlib import Path
from models.key import Key
from PIL.Image import Image
from models.user import User
from models.comment import Comment
from utils.database import get_database
from ..utils.config import Config

db = get_database()

@dataclass
class Post:
    _id: ObjectId = field(default_factory=lambda: None)
    id_thread: ObjectId
    id_author: ObjectId
    date: datetime = field(default_factory=lambda: datetime.now())
    title: str
    content: str
    medias: list[Path] = field(default_factory=list)
    keys: list[ObjectId] = field(default_factory=list)
    likes: list[ObjectId] = field(default_factory=list)
    comments: list[ObjectId] = field(default_factory=list)

    def save(self) -> None:
        if self._id is None:
            result = db.posts.insert_one(self.__dict__)
            self._id = result.inserted_id
        else:
            db.posts.update_one({"_id": self._id}, {"$set": self.__dict__})

    def delete(self) -> None:
        if self._id:
            db.posts.delete_one({"_id": self._id})

    def get_keys(self) -> list[Key]:
        return [Key.get_by_id(key_id) for key_id in self.keys]

    def get_likes(self) -> list[User]:
        return [User.get_by_id(user_id) for user_id in self.likes]

    def get_comments(self) -> list[Comment]:
        return [Comment.get_by_id(comment_id) for comment_id in self.comments]

    def get_medias(self) -> list[Image]:
        return [Image(Config.MEDIA_PATH / image) for image in self.medias]

    @staticmethod
    def get_by_id(user_id: str | ObjectId) -> 'Post' | None:
        data = db.posts.find_one({"_id": user_id})
        if data:
            return Post(**data)
        return None

    @staticmethod
    def all(limit: int = 30, **kwargs) -> Generator['User']:
        return (Post(**post) for post in db.posts.find({**kwargs, "title": {"$exists": True}}).limit(limit))
