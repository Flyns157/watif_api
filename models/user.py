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
    Classe représentant un utilisateur dans l'application, avec des informations de base telles que le rôle,
    le nom d'utilisateur, le mot de passe, l'email, et les intérêts. Gère l'interaction avec la base de données MongoDB,
    incluant l'insertion, la mise à jour, la suppression et la récupération de documents utilisateurs.

    Attributs :
        _id (ObjectId) : Identifiant unique de l'utilisateur, généré par MongoDB.
        id_role (ObjectId) : Identifiant du rôle de l'utilisateur.
        username (str) : Nom d'utilisateur.
        password (str | bytes) : Mot de passe chiffré de l'utilisateur.
        email (EmailStr) : Adresse e-mail de l'utilisateur.
        name (str) : Prénom de l'utilisateur.
        surname (str) : Nom de famille de l'utilisateur.
        pp (Path) : Chemin vers l'image de profil de l'utilisateur.
        birth_date (date) : Date de naissance de l'utilisateur.
        followed (list[ObjectId]) : Liste d'identifiants d'utilisateurs suivis.
        blocked (list[ObjectId]) : Liste d'identifiants d'utilisateurs bloqués.
        interests (list[ObjectId]) : Liste d'identifiants des intérêts de l'utilisateur.
        description (str) : Description de profil de l'utilisateur.
        status (str) : Statut actuel de l'utilisateur.

    Méthodes :
        __post_init__() : Chiffre le mot de passe s'il ne l'est pas déjà.
        hash_password(password: str | bytes) -> str : Retourne le mot de passe chiffré.
        check_password(password: str | bytes) -> bool : Vérifie si un mot de passe est correct.
        save() -> None : Insère ou met à jour l'utilisateur dans MongoDB.
        delete() -> None : Supprime l'utilisateur de MongoDB.
        update(**kwargs) -> None : Met à jour certains champs de l'utilisateur.
        get_role() -> Role : Récupère le rôle de l'utilisateur.
        get_followed() -> list['User'] : Récupère la liste des utilisateurs suivis.
        get_blocked() -> list['User'] : Récupère la liste des utilisateurs bloqués.
        get_interests() -> list[Interest] : Récupère la liste des intérêts de l'utilisateur.
        get_pp() -> Image : Récupère l'image de profil de l'utilisateur.
        get_by_id(user_id: str | ObjectId, strtype: bool = True) -> 'User | None' : Récupère un utilisateur par son ID.
        get_by_email(user_email: str | EmailStr) -> 'User | None' : Récupère un utilisateur par son e-mail.
        all(limit: int = 30, **kwargs) -> Generator['User'] : Récupère une liste d'utilisateurs selon des filtres et une limite.
        to_dto(private: bool = False) -> PublicUserDTO | PrivateUserDTO : Convertit les données de l'utilisateur en DTO public ou privé.
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
