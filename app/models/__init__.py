from .token import Token, TokenData
from .user import UserModel, GetUserModel, UpdateUserModel, UserCollection

# TODO: add models for other entities
# from .comment import CommentModel, CommentCollection, CreateCommentModel, UpdateCommentModel
# from .post import PostModel, PostCollection, CreatePostModel, UpdatePostModel
# from .interest import InterestModel, InterestCollection, CreateInterestModel, UpdateInterestModel
# from .key import KeyModel, KeyCollection, CreateKeyModel, UpdateKeyModel
# from .role import RoleModel, RoleCollection, CreateRoleModel, UpdateRoleModel
# from .thread import ThreadModel, ThreadCollection, CreateThreadModel, UpdateThreadModel




# depricated
from pydantic import BaseModel

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

class UserInDB(User):
    hashed_password: str
