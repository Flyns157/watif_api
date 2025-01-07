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
    User as UserModel, 
    UserRead,
    UserUpdate, 
    UserCollection,
    UserCreate,
)
from .post import (
    Post,
    Post as PostModel, 
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
    Interest as InterestModel, 
    InterestRead, 
    InterestCollection, 
    InterestCreate,
)
from .key import (
    key,
    Key as KeyModel, 
    KeyRead, 
    KeyCollection, 
    KeyCreate,
)
from .role import (
    Role, 
    Role as RoleModel, 
    RoleRead, 
    RoleCollection,
    RoleCreate, 
    RoleUpdate,
)
from .thread import (
    Thread, 
    Thread as ThreadModel, 
    ThreadRead, 
    ThreadCollection, 
    ThreadCreate, 
    ThreadUpdate,
)
