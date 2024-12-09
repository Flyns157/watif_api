from dataclasses import dataclass, field
from bson import ObjectId
from ..utils.database import get_database
from typing import Generator

db = get_database()

@dataclass
class Key:
    _id: ObjectId = field(default_factory=lambda: None)
    name: str

    def save(self) -> None:
        if self._id is None:
            result = db.keys.insert_one(self.__dict__)
            self._id = result.inserted_id
        else:
            db.keys.update_one({"_id": self._id}, {"$set": self.__dict__})

    def delete(self) -> None:
        if self._id:
            db.keys.delete_one({"_id": self._id})

    @staticmethod
    def get_by_id(key_id: str | ObjectId) -> 'Key | None':
        data = db.keys.find_one({"_id": key_id})
        if data:
            return Key(**data)
        return None

    @staticmethod
    def get_by_name(key_name: str | ObjectId) -> 'Key | None':
        data = db.keys.find_one({"name": key_name})
        if data:
            return Key(**data)
        return None

    @staticmethod
    def all(limit: int = 30, **kwargs) -> Generator['Key']:
        return (Key(**key) for key in db.keys.find(kwargs).limit(limit))
