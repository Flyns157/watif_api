from dataclasses import dataclass, field
from bson import ObjectId
from datetime import datetime
from pathlib import Path
from utils.database import get_database

db = get_database()

@dataclass
class Comment:
    _id: ObjectId = field(default_factory=lambda: None)
    id_thread: ObjectId
    id_author: ObjectId
    date: datetime = field(default_factory=lambda: datetime.now())
    content: str
    medias: list[Path]
    keys: list[ObjectId]
    likes: list[ObjectId]
    comments: list[ObjectId]

    def save(self):
        try:
            data = {k: str(v) if isinstance(v, ObjectId) else v for k, v in self.__dict__.items()}
            if self._id is None:
                result = db.posts.insert_one(data)
                self._id = result.inserted_id
            else:
                db.posts.update_one({"_id": self._id}, {"$set": data})
        except Exception as e:
            print(f"Error saving comment: {e}")

    def delete(self):
        try:
            if self._id:
                db.posts.delete_one({"_id": self._id})
        except Exception as e:
            print(f"Error deleting comment: {e}")

    @staticmethod
    def get_by_id(comment_id):
        data = db.posts.find_one({"_id": comment_id})
        if data:
            return Comment(**data)
        return None
