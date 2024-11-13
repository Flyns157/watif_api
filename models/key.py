from dataclasses import dataclass, field
from bson import ObjectId
from utils.database import get_database

db = get_database()

@dataclass
class Key:
    _id: ObjectId = field(default_factory=lambda: None)
    name: str

    def save(self):
        if self._id is None:
            result = db.keys.insert_one(self.__dict__)
            self._id = result.inserted_id
        else:
            db.keys.update_one({"_id": self._id}, {"$set": self.__dict__})

    def delete(self):
        if self._id:
            db.keys.delete_one({"_id": self._id})

    @staticmethod
    def get_by_id(key_id):
        data = db.keys.find_one({"_id": key_id})
        if data:
            return Key(**data)
        return None

    @staticmethod
    def get_by_name(key_name):
        data = db.keys.find_one({"name": key_name})
        if data:
            return Key(**data)
        return None
