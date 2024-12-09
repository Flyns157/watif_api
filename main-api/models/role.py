from dataclasses import dataclass, field
from bson import ObjectId
from ..utils.database import get_database
from typing import Generator

db = get_database()

@dataclass
class Role:
    _id: ObjectId = field(default_factory=lambda: None)
    name: str
    rights: list[str] = field(default_factory=list)
    extend: list[ObjectId] = field(default_factory=list)

    def save(self) -> None:
        if self._id is None:
            result = db.role.insert_one(self.__dict__)
            self._id = result.inserted_id
        else:
            db.roles.update_one({"_id": self._id}, {"$set": self.__dict__})

    def delete(self) -> None:
        if self._id:
            db.roles.delete_one({"_id": self._id})

    def update(self, **kwargs) -> None:
        editable = set(self.__dict__.keys()) - {"_id", "name", "extend"}
        for k, v in kwargs:
            if k in editable:
                self.__setattr__(k, v)
        self.save()

    @staticmethod
    def get_by_id(role_id: str | ObjectId) -> 'Role | None':
        data = db.roles.find_one({"_id": role_id})
        if data:
            return Role(**data)
        return None

    @staticmethod
    def get_by_name(role_name: str) -> 'Role | None':
        data = db.roles.find_one({"name": role_name})
        if data:
            return Role(**data)
        return None

    @staticmethod
    def all(limit: int = 30, **kwargs) -> Generator['Role']:
        return (Role(**key) for key in db.roles.find(kwargs).limit(limit))
