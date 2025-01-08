# Requirements.txt content:
# fastapi==0.104.1
# python-jose[cryptography]==3.3.0
# passlib[bcrypt]==1.7.4
# python-multipart==0.0.6
# motor==3.3.1
# pydantic==2.5.2
# uvicorn==0.24.0
# email-validator==2.1.0

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from enum import Enum
import asyncio
from bson import ObjectId
from typing_extensions import Annotated
from pydantic.functional_validators import BeforeValidator

# Constants
SECRET_KEY = "your-secret-key-here"  # In production, use a secure secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# MongoDB setup
MONGODB_URL = "mongodb://localhost:27017"
MONGODB_USER = "admin"
MONGODB_PASSWORD = "password"
MONGODB_DB_NAME = "auth_db"
ENABLE_REGISTRATION = True  # Feature flag for registration endpoint


from pydantic_core import CoreSchema
from pydantic import GetJsonSchemaHandler
# Custom ObjectId field for Pydantic v2
PyObjectId = Annotated[str, BeforeValidator(str)]

# Permission Enum
class Permission(str, Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"

# Pydantic Models
class MongoBaseModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        json_encoders = {
            ObjectId: str
        }
        populate_by_name = True

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str
    permissions: List[Permission] = []

class UserDB(MongoBaseModel, UserBase):
    hashed_password: str
    is_active: bool = True
    refresh_token: Optional[str] = None
    permissions: List[Permission] = []

class UserOut(MongoBaseModel, UserBase):
    is_active: bool
    permissions: List[Permission]

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    permissions: List[str] = []

class RegistrationResponse(BaseModel):
    message: str
    user_id: str
    email: str
    username: str

class ErrorResponse(BaseModel):
    detail: str

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Database connection management
class MongoManager:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

    async def connect_to_database(self):
        try:
            # Create connection URL with authentication
            if MONGODB_USER and MONGODB_PASSWORD:
                connection_url = f"mongodb://{MONGODB_USER}:{MONGODB_PASSWORD}@localhost:27017/{MONGODB_DB_NAME}?authSource=admin"
            else:
                connection_url = MONGODB_URL

            # Connect to MongoDB
            self.client = AsyncIOMotorClient(connection_url)
            
            # Test the connection
            await self.client.admin.command('ping')
            
            self.db = self.client[MONGODB_DB_NAME]
            
            # Create indexes
            try:
                await self.db.users.create_index("email", unique=True)
                await self.db.users.create_index("username", unique=True)
                print("Indexes created successfully")
            except Exception as e:
                print(f"Error creating indexes: {e}")
                # Don't raise the error as indexes might already exist
                
        except Exception as e:
            print(f"Could not connect to MongoDB: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not connect to database"
            )

    async def close_database_connection(self):
        if self.client is not None:
            self.client.close()

mongodb = MongoManager()

async def get_database() -> AsyncIOMotorDatabase:
    return mongodb.db

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> UserDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user_doc = await db.users.find_one({"username": username})
    if user_doc is None:
        raise credentials_exception
        
    return UserDB(**user_doc)

def verify_permission(required_permission: Permission):
    async def permission_dependency(current_user: UserDB = Depends(get_current_user)):
        if required_permission not in current_user.permissions and Permission.ADMIN not in current_user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return permission_dependency

# FastAPI app
app = FastAPI(title="FastAPI Auth System with Motor")

# Startup and shutdown events
@app.on_event("startup")
async def startup_db_client():
    await mongodb.connect_to_database()

@app.on_event("shutdown")
async def shutdown_db_client():
    await mongodb.close_database_connection()

# Auth endpoints
@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    user_doc = await db.users.find_one({"username": form_data.username})
    if not user_doc or not verify_password(form_data.password, user_doc["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_doc["username"]}, 
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user_doc["username"]})
    
    # Update refresh token in database
    await db.users.update_one(
        {"_id": user_doc["_id"]},
        {"$set": {"refresh_token": refresh_token}}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@app.post("/refresh-token", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_doc = await db.users.find_one({
            "username": username,
            "refresh_token": refresh_token
        })
        
        if not user_doc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": username},
            expires_delta=access_token_expires
        )
        new_refresh_token = create_refresh_token(data={"sub": username})
        
        await db.users.update_one(
            {"_id": user_doc["_id"]},
            {"$set": {"refresh_token": new_refresh_token}}
        )
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

# User management endpoints
@app.post("/users/", response_model=UserOut)
async def create_user(
    user: UserCreate, 
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    # Check if user exists
    existing_user = await db.users.find_one({
        "$or": [
            {"email": user.email},
            {"username": user.username}
        ]
    })
    if existing_user:
        raise HTTPException(
            status_code=400, 
            detail="Email or username already registered"
        )
    
    # Create new user
    user_data = {
        "email": user.email,
        "username": user.username,
        "hashed_password": get_password_hash(user.password),
        "is_active": True,
        "permissions": user.permissions
    }
    
    result = await db.users.insert_one(user_data)
    user_data["_id"] = result.inserted_id
    
    return UserOut(**user_data)

@app.get("/users/me/", response_model=UserOut)
async def read_users_me(current_user: UserDB = Depends(get_current_user)):
    return current_user

# Protected endpoints example
@app.get("/protected/read-only/")
async def read_protected_data(
    current_user: UserDB = Depends(verify_permission(Permission.READ))
):
    return {
        "message": "You have read access!",
        "user": current_user.username
    }

@app.post("/protected/write/")
async def write_protected_data(
    current_user: UserDB = Depends(verify_permission(Permission.WRITE))
):
    return {
        "message": "You have write access!",
        "user": current_user.username
    }

@app.get("/protected/admin/")
async def admin_protected_data(
    current_user: UserDB = Depends(verify_permission(Permission.ADMIN))
):
    return {
        "message": "You have admin access!",
        "user": current_user.username
    }

@app.post(
    "/register", 
    response_model=RegistrationResponse,
    responses={
        400: {"model": ErrorResponse},
        403: {"model": ErrorResponse}
    }
)
async def register_user(
    user: UserCreate,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    if not ENABLE_REGISTRATION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration is currently disabled"
        )

    # Validate email format
    if not user.email or '@' not in user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )

    # Validate username length
    if len(user.username) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be at least 3 characters long"
        )

    # Validate password strength
    if len(user.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )

    # Check if user exists
    existing_user = await db.users.find_one({
        "$or": [
            {"email": user.email},
            {"username": user.username}
        ]
    })
    
    if existing_user:
        if existing_user["email"] == user.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

    # Create new user with default READ permission
    user_data = {
        "email": user.email,
        "username": user.username,
        "hashed_password": get_password_hash(user.password),
        "is_active": True,
        "permissions": [Permission.READ] if not user.permissions else user.permissions
    }

    try:
        result = await db.users.insert_one(user_data)
        
        return RegistrationResponse(
            message="Registration successful",
            user_id=str(result.inserted_id),
            email=user.email,
            username=user.username
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
