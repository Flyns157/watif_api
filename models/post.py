from dataclasses import dataclass, field
from bson import ObjectId
from datetime import datetime
from pathlib import Path
from utils.database import get_database

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

    def save(self):
        if self._id is None:
            result = db.posts.insert_one(self.__dict__)
            self._id = result.inserted_id
        else:
            db.posts.update_one({"_id": self._id}, {"$set": self.__dict__})

    def delete(self):
        if self._id:
            db.posts.delete_one({"_id": self._id})

    @staticmethod
    def get_by_id(user_id):
        data = db.posts.find_one({"_id": user_id})
        if data:
            return Post(**data)
        return None
