from typing_extensions import Annotated
from pydantic import BeforeValidator
from uuid import UUID
from datetime import date


# Custom UUID field for Pydantic v2
PyUUID = Annotated[str, BeforeValidator(lambda v: str(UUID(v)) if not isinstance(v, UUID) else str(v))]
Date = Annotated[str, BeforeValidator(lambda v: str(date.fromisoformat(v)) if not isinstance(v, date) else str(v))]


from .token import Token, TokenData
from .user import (
    User, 
    UserRead,
    UserUpdate, 
    UserCollection,
    UserCreate,
)
from .post import (
    Post, 
    PostCollection, 
    PostCreate, 
    PostUpdate, 
    Comment, 
    CommentCollection, 
    CommentCreate, 
    CommentUpdate,
    Like,
    Dislike,
)
from .interest import (
    Interest, 
    InterestRead, 
    InterestCollection, 
    InterestCreate,
)
from .key import (
    Key, 
    KeyRead, 
    KeyCollection, 
    KeyCreate,
)
from .role import (
    Role, 
    RoleRead, 
    RoleCollection,
    RoleCreate, 
    RoleUpdate,
)
from .thread import (
    Thread, 
    ThreadRead, 
    ThreadCollection, 
    ThreadCreate, 
    ThreadUpdate,
)
