from dataclasses import dataclass, field
from bson import ObjectId
from pydantic import EmailStr
from datetime import date
from pathlib import Path
from models.interest import Interest
from models.role import Role
from utils.database import get_database
import bcrypt
from dtos.user_dto import PublicUserDTO, PrivateUserDTO
from ..app import Config
from PIL.Image import Image
from typing import Generator
from utils.helpers import isobjectid


db = get_database()

@dataclass
class User:
    """
    Class representing a user in the application, with basic information such as role, username, password, email, and interests.
    Manages interaction with the MongoDB database, including insertion, update, deletion, and retrieval of user documents.

    Attributes:
        _id (ObjectId): Unique identifier for the user, generated by MongoDB.
        id_role (ObjectId): Identifier for the user's role.
        username (str): Username of the user.
        password (str | bytes): Encrypted password of the user.
        email (EmailStr): Email address of the user.
        name (str): First name of the user.
        surname (str): Last name of the user.
        pp (Path): Path to the user's profile picture.
        birth_date (date): Birthdate of the user.
        followed (list[ObjectId]): List of identifiers for users being followed.
        blocked (list[ObjectId]): List of identifiers for blocked users.
        interests (list[ObjectId]): List of identifiers for the user's interests.
        description (str): Profile description of the user.
        status (str): Current status of the user.

    Methods:
        __post_init__(): Encrypts the password if it isn't already encrypted.
        hash_password(password: str | bytes) -> str: Returns the encrypted password.
        check_password(password: str | bytes) -> bool: Verifies if a password is correct.
        save() -> None: Inserts or updates the user in MongoDB.
        delete() -> None: Deletes the user from MongoDB.
        update(**kwargs) -> None: Updates certain fields of the user.
        get_role() -> Role: Retrieves the user's role.
        get_followed() -> list['User']: Retrieves the list of followed users.
        get_blocked() -> list['User']: Retrieves the list of blocked users.
        get_interests() -> list[Interest]: Retrieves the list of the user's interests.
        get_pp() -> Image: Retrieves the user's profile picture.
        get_by_id(user_id: str | ObjectId, strtype: bool = True) -> 'User | None': Retrieves a user by their ID.
        get_by_email(user_email: str | EmailStr) -> 'User | None': Retrieves a user by their email.
        all(limit: int = 30, **kwargs) -> Generator['User']: Retrieves a list of users based on filters and a limit.
        to_dto(private: bool = False) -> PublicUserDTO | PrivateUserDTO: Converts the user's data to a public or private DTO.
    """
    _id: ObjectId = field(default_factory=lambda: None)  # Par défaut None, MongoDB l’attribuera automatiquement
    id_role: ObjectId
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
    status: str = ""
@dataclass
class User:
    # ...

    def __post_init__(self):
        """Encrypt the user's password after initialization if it's not already hashed."""
        if not self.password.startswith('$2b$'):
            self.password = self.hash_password(self.password)

    @staticmethod
    def hash_password(password: str | bytes) -> str:
        """Hash the user's password using bcrypt.
        
        Args:
            password: The plain-text password as a string or bytes.

        Returns:
            str: The hashed password.
        """
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password: str | bytes) -> bool:
        """Check if the provided password matches the stored hashed password.
        
        Args:
            password: The plain-text password to check.

        Returns:
            bool: True if the password is correct, False otherwise.
        """
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

    def save(self) -> None:
        """Save the user to the database. Insert a new document if `_id` is None, otherwise update the existing one."""
        if self._id is None:
            result = db.users.insert_one(self.__dict__)
            self._id = result.inserted_id
        else:
            db.users.update_one({"_id": self._id}, {"$set": self.__dict__})

    def delete(self):
        """Delete the user from the database."""
        if self._id:
            db.users.delete_one({"_id": self._id})

    def update(self, **kwargs) -> None:
        """Update the user's attributes and save the changes.
        
        Args:
            kwargs: Fields and values to update.
        """
        editable_fields = set(self.__dict__.keys()) - {"_id", "email", "name", "surname", "birth_date"}
        for k, v in kwargs.items():
            if k in editable_fields:
                if k == "password":
                    self.password = self.hash_password(v)
                elif k == "role" and not isobjectid(v):
                    self.role = Role.get_by_name(v)._id
                else:
                    setattr(self, k, v)
        self.save()

    def get_role(self) -> Role:
        """Retrieve the user's role from the database.
        
        Returns:
            Role: The role object associated with the user.
        """
        return Role.get_by_id(self.id_role)

    def get_followed(self) -> list['User']:
        """Retrieve the list of users followed by this user.
        
        Returns:
            list[User]: List of User objects that are followed.
        """
        return [User.get_by_id(user_id) for user_id in self.followed]

    def get_blocked(self) -> list['User']:
        """Retrieve the list of users blocked by this user.
        
        Returns:
            list[User]: List of User objects that are blocked.
        """
        return [User.get_by_id(user_id) for user_id in self.blocked]

    def get_interests(self) -> list[Interest]:
        """Retrieve the list of interests associated with the user.
        
        Returns:
            list[Interest]: List of Interest objects.
        """
        return [Interest.get_by_id(user_id) for user_id in self.followed]

    def get_pp(self) -> Image:
        """Get the user's profile picture as an Image object.
        
        Returns:
            Image: The profile picture of the user.
        """
        return Image(Config.MEDIA_PATH / self.pp)

    @staticmethod
    def get_by_id(user_id: str | ObjectId, strtype: bool = True):
        """Retrieve a user by their unique identifier.
        
        Args:
            user_id: The unique identifier of the user.
            strtype: If True, return as a User object; if False, convert fields to ensure type consistency.

        Returns:
            User or None: The user if found, otherwise None.
        """
        data = db.users.find_one({"_id": user_id})
        if data:
            if strtype:
                return User(**data)
            # Type conversions for consistency
            data["_id"] = ObjectId(data["_id"])
            data["id_role"] = ObjectId(data["id_role"])
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
        """Retrieve a user by their email address.
        
        Args:
            user_email: The email of the user.

        Returns:
            User or None: The user if found, otherwise None.
        """
        data = db.users.find_one({"email": user_email})
        if data:
            return User(**data)
        return None
    
    @staticmethod
    def all(limit: int = 30, **kwargs) -> Generator['User']:
        """Retrieve all users matching given filters.
        
        Args:
            limit: The maximum number of users to retrieve.
            kwargs: Additional filters for retrieving users.

        Returns:
            Generator[User]: A generator of User objects.
        """
        if 'role' in kwargs and not isobjectid(kwargs['role']):
            kwargs['role'] = Role.get_by_name(kwargs['role'])._id
        return (User(**user) for user in db.users.find(kwargs).limit(limit))

    def to_dto(self, private: bool = False) -> PublicUserDTO | PrivateUserDTO:
        """Convert the user to a data transfer object (DTO) for external use.
        
        Args:
            private: If True, include private user details in the DTO.

        Returns:
            PublicUserDTO or PrivateUserDTO: The DTO representation of the user.
        """
        if private:
            return PrivateUserDTO(
                id=str(self._id),
                role=str(self.get_role().name),
                username=self.username,
                email=self.email,
                name=self.name,
                surname=self.surname,
                pp=self.pp,
                birth_date=self.birth_date,
                followed=[str(f) for f in self.followed],
                blocked=[str(b) for b in self.blocked],
                interests=[str(i) for i in self.interests],
                description=self.description,
                status=self.status
            )
        else:
            return PublicUserDTO(
                id=str(self._id),
                role=str(self.get_role().name),
                username=self.username,
                pp=self.pp,
                birth_date=self.birth_date,
                followed=[str(f) for f in self.followed],
                interests=[str(i) for i in self.interests],
                description=self.description,
                status=self.status
            )
