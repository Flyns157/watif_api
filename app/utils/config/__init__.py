from pydantic import BaseModel
from dotenv import load_dotenv
import os

from .modes import Mode, Stage


load_dotenv()


class Settings:
    MONGODB_URI: str = os.getenv("MONGODB_URI")
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE")
    
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
    
    MODE: Mode = Mode(os.getenv("MODE"))
    STAGE: Stage = Stage(os.getenv("STAGE"))

    DOMAIN_NAME = os.getenv("DOMAIN_NAME")
