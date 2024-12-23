from pydantic import BaseModel, UUID5


class Interest(BaseModel):
    """
    Interest model
    """
    name: str

class InterestRead(Interest):
    """
    Interest public model
    """
    ...

class InterestCreate(Interest):
    """
    Interest create model
    """
    ...

class InterestCollection(BaseModel):
    """
    Interest collection model
    """
    interests: list[InterestRead]
