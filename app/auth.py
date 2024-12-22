from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from pydantic import EmailStr, UUID5
from jose import JWTError, jwt


from .database.mongodb import user_collection, role_collection
from .models import UserModel, TokenData
from .utils.config import Settings


SECRET_KEY = Settings.JWT_SECRET_KEY
ALGORITHM = Settings.JWT_ALGORITHM

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


async def get_user(identifier: str | EmailStr) -> UserModel | None:
    try:
        EmailStr._validate(identifier)
        user = await user_collection.find_one({"email": identifier})
    except ValueError:
        user = await user_collection.find_one({"username": identifier})

    if user:
        return UserModel(**user)


async def authenticate_user(identifier: str | EmailStr, password: str) -> UserModel | None:
    if (user := await get_user(identifier)) and verify_password(password, user.hashed_password):
        return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credential_exception = HTTPException(   status_code=status.HTTP_401_UNAUTHORIZED,
                                            detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credential_exception

        token_data = TokenData(username=username)
    except JWTError:
        raise credential_exception

    user = await get_user(token_data.username)
    if user is None:
        raise credential_exception

    return user


async def get_current_active_user(current_user: UserModel = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Disabled user")

    return current_user


async def get_permissions(user: UserModel):
    roles: list = await role_collection.find().to_list()

    def index_role(roles: list) -> dict:
        return {role["name"]: role for role in roles}

    roles = index_role(roles)

    def get_rights(role_name: str):
        return [] if not (role := roles.get(role_name)) else role["rights"] + [p for r in role["inherits"] for p in get_rights(r)]

    return get_rights(user.role_name)


async def has_permissions(user: UserModel, permission: str) -> bool:
    roles: list = await role_collection.find().to_list()

    def index_role(roles: list) -> dict:
        return {role["name"]: role for role in roles}

    roles = index_role(roles)

    def has_right(role_name: str, permission: str) -> bool:
        if not (role := roles.get(role_name)):
            return False
        if permission in role["rights"]:
            return True
        return any(has_right(r, permission) for r in role["inherits"])

    return has_right(user.role_name, permission)


async def corresponds(user: UserModel, be_user: str | UUID5 = None, have_permission: str = None, have_role: str = None) -> bool:
    if be_user and str(user.uuid) != str(be_user):
        return False

    if have_permission and not await has_permissions(user, have_permission):
        return False

    if have_role and user.role_name != have_role:
        return False

    return True
