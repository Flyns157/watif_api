from dataclasses import dataclass, field
from bson import ObjectId
from pydantic import EmailStr
from datetime import date
from pathlib import Path
from models.interest import Interest
from utils.database import get_database
import bcrypt
from dtos.user_dto import UserDTO
from ..app import Config
from PIL.Image import Image
from typing import Generator


db = get_database()

@dataclass
class User:
    _id: ObjectId = field(default_factory=lambda: None)  # Par défaut None, MongoDB l’attribuera automatiquement
    role: ObjectId
    username: str
    password: str | bytes
    email: EmailStr
    name: str
    surname: str
    pp: Path
    birth_date: date
    followed: list[ObjectId] = field(default_factory=list)
    blocked: list[ObjectId] = field(default_factory=list)
    interests: list[ObjectId] = field(default_factory=list)
    description: str = ""
    status: str = "new"

    def __post_init__(self):
        # Chiffrer le mot de passe si non chiffré
        if not self.password.startswith('$2b$'):
            self.password = self.hash_password(self.password)

    @staticmethod
    def hash_password(password: str | bytes) -> str:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password: str | bytes) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

    def save(self) -> None:
        # Si `_id` est None, nous créons un nouveau document dans MongoDB
        if self._id is None:
            result = db.users.insert_one(self.__dict__)
            self._id = result.inserted_id  # MongoDB génère et retourne l'ID
        else:
            # Mise à jour du document existant
            db.users.update_one({"_id": self._id}, {"$set": self.__dict__})

    def delete(self):
        if self._id:
            db.users.delete_one({"_id": self._id})

    def update(self, **kwargs) -> None:
        editable = set(self.__dict__.keys()) - {"email", "name", "surname", "birth_date"}
        for k, v in kwargs:
            if k in editable:
                self.__setattr__(k, v)
        self.save()

    def get_followed(self) -> list['User']:
        return [User.get_by_id(user_id) for user_id in self.followed]

    def get_blocked(self) -> list['User']:
        return [User.get_by_id(user_id) for user_id in self.blocked]

    def get_interests(self) -> list[Interest]:
        return [Interest.get_by_id(user_id) for user_id in self.followed]

    def get_pp(self):
        return Image(Config.MEDIA_PATH / self.pp)

    @staticmethod
    def get_by_id(user_id: str | ObjectId, strtype: bool = True):
        data = db.users.find_one({"_id": user_id})
        if data:
            if strtype:
                return User(**data)
            # Conversions pour assurer que chaque champ est du bon type
            data["_id"] = ObjectId(data["_id"])
            data["role"] = ObjectId(data["role"])
            data["email"] = EmailStr(data.get("email", None))
            data["pp"] = Path(data.get("pp", None))
            data["birth_date"] = date.fromisoformat(data["birth_date"]) if isinstance(data["birth_date"], str) else data["birth_date"]
            data["followed"] = [ObjectId(like) for like in data.get("followed", [])]
            data["blocked"] = [ObjectId(like) for like in data.get("blocked", [])]
            data["interests"] = [ObjectId(like) for like in data.get("interests", [])]
            
            return User(**data)
        return None

    @staticmethod
    def get_by_email(user_email: str | EmailStr) -> 'User':
        data = db.users.find_one({"email": user_email})
        if data:
            return User(**data)
        return None

    @staticmethod
    def all() -> Generator['User']:
        return (User(**user) for user in db.users.find())

    def to_dto(self) -> UserDTO:
        return UserDTO(
            id=str(self._id),
            role=str(self.role),
            username=self.username,
            mail=self.mail,
            name=self.name,
            surname=self.surname,
            pp=self.pp,
            birthDate=self.birthDate,
            followed=[str(f) for f in self.followed],
            blocked=[str(b) for b in self.blocked],
            interests=[str(i) for i in self.interests],
            description=self.description,
            status=self.status
        )