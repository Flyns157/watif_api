from typing_extensions import Annotated
from pydantic import BeforeValidator
from uuid import UUID
from datetime import date

from .token import Token, TokenData
from .user import (
    User as UserModel,
    UserRead,
    UserUpdate,
    UserCollection,
    UserCreate,
)
from .post import (
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
    Interest as InterestModel,
    InterestRead,
    InterestCollection,
    InterestCreate,
)
from .key import (
    Key as KeyModel,
    KeyRead,
    KeyCollection,
    KeyCreate,
)
from .role import (
    Role as RoleModel,
    RoleRead,
    RoleCollection,
    RoleCreate,
    RoleUpdate,
)
from .thread import (
    Thread as ThreadModel,
    ThreadRead,
    ThreadCollection,
    ThreadCreate,
    ThreadUpdate,
)


# Custom UUID field for Pydantic v2
PyUUID = Annotated[
    str,
    BeforeValidator(
        lambda v: str(UUID(v)) if not isinstance(v, UUID) else str(v)
    )
]
Date = Annotated[
    str,
    BeforeValidator(
        lambda v: str(date.fromisoformat(v)) if not isinstance(v, date) else str(v)
    )
]


__all__ = [
    "Token",
    "TokenData",
    "UserModel",
    "UserRead",
    "UserUpdate",
    "UserCollection",
    "UserCreate",
    "PostModel",
    "PostCollection",
    "PostCreate",
    "PostUpdate",
    "Comment",
    "CommentCollection",
    "CommentCreate",
    "CommentUpdate",
    "Like",
    "Dislike",
    "InterestModel",
    "InterestRead",
    "InterestCollection",
    "InterestCreate",
    "KeyModel",
    "KeyRead",
    "KeyCollection",
    "KeyCreate",
    "RoleModel",
    "RoleRead",
    "RoleCollection",
    "RoleCreate",
    "RoleUpdate",
    "ThreadModel",
    "ThreadRead",
    "ThreadCollection",
    "ThreadCreate",
    "ThreadUpdate",
    "PyUUID",
    "Date",
]
