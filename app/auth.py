from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from pydantic import EmailStr, UUID5
from jose import JWTError, jwt


from .utils.config import Settings
from .models import User
from . import mongodb


SECRET_KEY = Settings.JWT_SECRET_KEY
ALGORITHM = Settings.JWT_ALGORITHM

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


NOT_AUTHORIZED_ERROR = HTTPException(status_code=403, detail="Not authorized to perform this action")


def verify_password(plain_password, hashed_password):
    """
    Verify the hashed password with the plain password.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """
    Hash the password.
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """
    Create an access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def authenticate_user(identifier: str | EmailStr | UUID5, password: str) -> User | None:
    """
    Authenticate the user with the identifier and password.
    """
    for field in ("uuid", "username", "email"):
        if (user := await mongodb.db.users.find_one({field: identifier})):
            return User(**user) if verify_password(password, user["hashed_password"]) else None


async def current_user(token: str = Depends(oauth2_scheme)) -> User | None:
    """
    Get the current user from the token.
    """
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        uuid: str = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])["sub"]
        if uuid is None:
            raise credential_exception
    except JWTError:
        raise credential_exception

    if (user := await mongodb.db.users.find_one({"uuid": uuid})):
        if user.get("disabled"):
            raise HTTPException(status_code=400, detail="Disabled user")

        return User(**user)

    raise credential_exception


async def corresponds(user: User, raise_exception: bool = False, **kwargs) -> bool | HTTPException:
    """
    Check if the user corresponds to the conditions.
    """
    if not isinstance(user, User):
        raise TypeError(f"user must be an instance of User, not a {type(user)}")

    for k, v in kwargs.items():
        if k == "permissions":
            for p in v:
                if not await has_permissions(user, p):
                    if raise_exception:
                        raise NOT_AUTHORIZED_ERROR
                    return False

        elif k == "permission":
            if not await has_permissions(user, v):
                if raise_exception:
                    raise NOT_AUTHORIZED_ERROR
                return False
        
        elif getattr(user, k)!= v:
            if raise_exception:
                raise NOT_AUTHORIZED_ERROR
            return False

    return True


def current_user_like(**kwargs):
    """
    Get the current user from the token and check if it corresponds to the conditions.
    """
    
    async def process_like(user: User = Depends(current_user)) -> User | None:
        if await corresponds(user=user, raise_exception=True, **kwargs):
            return user

    return process_like


def current_user_likes(*args):
    """
    Get the current user from the token and check if it corresponds to the conditions (a list of conditions shema / types of users).
    """
        
    from . import main_logger
    main_logger.warning(f"current_user_likes args : {args}")

    async def process_likes(user: User = Depends(current_user)) -> User | None:
        
        from . import main_logger
        main_logger.warning(f"current_user_likes args : {args}")
        
        for conditions in args:
            try:
                if await corresponds(user=user, raise_exception=True, **conditions):
                    return user
            except HTTPException:
                continue

        raise NOT_AUTHORIZED_ERROR

    return process_likes


async def get_permissions(user: User) -> set:
    """
    Get the permissions of the user.
    """

    if not isinstance(user, User):
        raise TypeError("user must be an instance of User")

    roles: list = await mongodb.db.roles.find().to_list(100)

    def index_role(roles: list) -> dict:
        return {role["name"]: role for role in roles}

    roles = index_role(roles)

    def get_rights(role: str):
        return [] if not (role := roles.get(role)) else role["rights"] + [p for r in role["inherits"] for p in get_rights(r)]

    return set(get_rights(user.role))


async def has_permissions(user: User, permission: str) -> bool:
    """
    Check if the user has the permission.
    """

    if not isinstance(user, User):
        raise TypeError("user must be an instance of User")

    roles: list = await mongodb.db.roles.find().to_list(100)

    def index_role(roles: list) -> dict:
        return {role["name"]: role for role in roles}

    roles = index_role(roles)

    def has_right(role: str, permission: str) -> bool:
        if not (role := roles.get(role)):
            return False
        if permission in role["rights"]:
            return True
        return any(has_right(r, permission) for r in role["inherits"]) if role["inherits"] else False

    return has_right(user.role, permission)
