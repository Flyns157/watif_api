from dataclasses import dataclass, field
from bson import ObjectId
from utils.database import get_database

db = get_database()

@dataclass
class Thread:
    _id: ObjectId = field(default_factory=lambda: None)
    name: str
    id_owner: ObjectId
    admins: list[ObjectId] = field(default_factory=list)
    members: list[ObjectId] = field(default_factory=list)

    def save(self):
        if self._id is None:
            result = db.threads.insert_one(self.__dict__)
            self._id = result.inserted_id
        else:
            db.threads.update_one({"_id": self._id}, {"$set": self.__dict__})

    def delete(self):
        if self._id:
            db.threads.delete_one({"_id": self._id})

    @staticmethod
    def get_by_id(thread_id):
        data = db.threads.find_one({"_id": thread_id})
        if data:
            return Thread(**data)
        return None
