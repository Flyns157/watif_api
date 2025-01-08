import os
import configparser
from dotenv import load_dotenv

from .modes import Mode, Stage


load_dotenv()


class Settings:
    MONGODB_URI: str = os.getenv("MONGODB_URI")
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE")
    MONGODB_USER: str = os.getenv("MONGODB_USER")
    MONGODB_PASSWORD: str = os.getenv("MONGODB_PASSWORD")
    
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
    
    MODE: Mode = Mode(os.getenv("MODE"))
    STAGE: Stage = Stage(os.getenv("STAGE"))

    DOMAIN_NAME: str = os.getenv("DOMAIN_NAME")

    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD")


# Créer une instance de ConfigParser
config = configparser.ConfigParser()

# Lire le fichier de configuration
config.read('main.ini')
