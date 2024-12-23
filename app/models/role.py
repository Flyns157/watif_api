from pydantic import BaseModel


class Role(BaseModel):
    """
    A class representing a role in the system.
    """
    name: str
    rights: list[str] | None
    inherits: list[str] | None = None

class RoleRead(Role):
    """
    A class representing a role to be returned in a response.
    """
    ...


class RoleCreate(Role):
    """
    A class representing a role to be created in the system.
    """
    ...


class RoleUpdate(BaseModel):
    """
    A class representing a role to be updated in the system.
    """
    rights: list[str] | None = None
    inherits: list[str] | None = None


class RoleCollection(BaseModel):
    """
    A class representing a collection of roles in the system.
    """
    roles: list[RoleRead]
