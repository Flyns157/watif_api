from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    MEDIA_PATH = os.getenv('MEDIA_PATH') or 'media'
    TOKEN_EXPIRES = int(os.getenv('TOKEN_EXPIRES')) or 3600
    