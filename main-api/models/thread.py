from dataclasses import dataclass, field
from bson import ObjectId
from .post import Post
from .user import User
from typing import Generator
from ..utils.database import get_database

db = get_database()

@dataclass
class Thread:
    _id: ObjectId = field(default_factory=lambda: None)
    name: str
    public: bool
    id_owner: ObjectId
    moderators: list[ObjectId] = field(default_factory=list)
    members: list[ObjectId] = field(default_factory=list)

    def save(self) -> None:
        if self._id is None:
            result = db.threads.insert_one(self.__dict__)
            self._id = result.inserted_id
        else:
            db.threads.update_one({"_id": self._id}, {"$set": self.__dict__})

    def delete(self) -> None:
        if self._id:
            db.threads.delete_one({"_id": self._id})

    def update(self, **kwargs) -> None:
        editable = set(self.__dict__.keys()) - {"_id", "id_owner"}
        for k, v in kwargs.items():
            if k in editable:
                self.__setattr__(k, v)
            else:
                raise ValueError(f"Field '{k}' is not editable")
        self.save()

    def get_moderators(self) -> list[User]:
        return [User.get_by_id(user_id) for user_id in self.moderators]

    def get_members(self) -> list[User]:
        return [User.get_by_id(user_id) for user_id in self.members]

    def get_posts(self) -> list[Post]:
        return [Post(**post) for post in db.posts.find({"id_thread": self._id})]

    def add_member(self, id_user: ObjectId) -> bool:
        if id_user in self.members:
            return False
        self.members.append(id_user)
        self.save()
        return True

    def del_member(self, id_user: ObjectId) -> bool:
        if id_user not in self.members:
            return False
        self.members.remove(id_user)
        self.save()
        return True

    def add_moderator(self, id_user: ObjectId) -> bool:
        if id_user in self.moderators:
            return False
        self.moderators.append(id_user)
        self.save()
        return True

    def del_moderator(self, id_user: ObjectId) -> bool:
        if id_user not in self.moderators:
            return False
        self.moderators.remove(id_user)
        self.save()
        return True

    def make_public(self) -> None:
        self.public = True
        self.save()

    def make_private(self) -> None:
        self.public = False
        self.save()

    @staticmethod
    def get_by_id(thread_id: str | ObjectId) -> 'Thread | None':
        data = db.threads.find_one({"_id": thread_id})
        if data:
            return Thread(**data)
        return None

    @staticmethod
    def all(limit: int = 30, **kwargs) -> Generator['Thread']:
        return (Thread(**thread) for thread in db.threads.find(kwargs).limit(limit))
