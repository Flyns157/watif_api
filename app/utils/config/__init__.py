from pydantic import BaseModel
from .modes import Mode, Stage


class Settings(BaseModel):
    debug: bool = False
    testing: bool = False
    database_url: str = "sqlite://test.db"
    
    jwt_secret_key: str = "83daa0256a2289b0fb23693bf1f6034d44396675749244721a2b20e896e11662"
    jwt_algorithm: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    mode: Mode = Mode.MAIN
    stage: Stage = Stage.DEVELOPMENT
