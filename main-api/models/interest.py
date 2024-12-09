from dataclasses import dataclass, field
from bson import ObjectId
from utils.database import get_database
from typing import Generator

db = get_database()

@dataclass
class Interest:
    _id: ObjectId = field(default_factory=lambda: None)
    name: str

    def save(self) -> None:
        if self._id is None:
            result = db.users.insert_one(self.__dict__)
            self._id = result.inserted_id
        else:
            db.users.update_one({"_id": self._id}, {"$set": self.__dict__})

    def delete(self) -> None:
        if self._id:
            db.interests.delete_one({"_id": self._id})

    @staticmethod
    def get_by_id(interest_id: str | ObjectId) -> 'Interest' | None:
        data = db.interests.find_one({"_id": interest_id})
        if data:
            return Interest(**data)
        return None

    @staticmethod
    def get_by_name(interest_name: str) -> 'Interest' | None:
        data = db.interests.find_one({"name": interest_name})
        if data:
            return Interest(**data)
        return None

    @staticmethod
    def all(limit: int = 30, **kwargs) -> Generator['Interest']:
        return (Interest(**key) for key in db.interests.find(kwargs).limit(limit))
