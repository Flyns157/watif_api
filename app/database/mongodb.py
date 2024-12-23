from pydantic import BaseModel
import motor.motor_asyncio

from ..utils.config import Settings
from ..models.role import Role


# Set up the MongoDB connection
client = motor.motor_asyncio.AsyncIOMotorClient(Settings.MONGODB_URI)
client.uuid_representation = 5
db = client[Settings.MONGODB_DATABASE]


# User collection
user_collection = db.get_collection("users")

# Role collection
role_collection = db.get_collection("roles")


async def initialize_database():
    # Create indexes
    await user_collection.create_index("uuid", unique=True)
    await user_collection.create_index("username", unique=True)
    await user_collection.create_index("email", unique=True)

    await role_collection.create_index("name", unique=True)

    # Create default roles if they don't exist
    existing_role = await role_collection.find_one({"name": "user"})
    if existing_role is None:
        role_collection.insert_one(
            Role(name="user" , rights=["update:self", "delete:self"]).model_dump()
        )

    existing_role = await role_collection.find_one({"name": "admin"})
    if existing_role is None:
        role_collection.insert_one(
            Role(name="admin" , rights=["*", "create:all", "read:all", "update:all", "delete:all", ], inherits=["user"]).model_dump()
        )

# TODO: Add more methods for CRUD operations on other collections (and redefine the security model)
def get_collection(collection_name: str | BaseModel):
    if issubclass(collection_name, BaseModel):
        collection_name = collection_name.__name__.lower()
    return db.get_collection(collection_name)

class MongoModel:
    collection_name: str | BaseModel

    @classmethod
    async def find_one(cls, query: dict):
        collection = get_collection(cls.collection_name)
        return await collection.find_one(query)

    @classmethod
    async def find(cls, query: dict):
        collection = get_collection(cls.collection_name)
        return await collection.find(query)

    @classmethod
    async def insert_one(cls, document: dict):
        collection = get_collection(cls.collection_name)
        return await collection.insert_one(document)

    @classmethod
    async def update_one(cls, query: dict, update: dict):
        collection = get_collection(cls.collection_name)
        return await collection.update_one(query, update)

    @classmethod
    async def delete_one(cls, query: dict):
        collection = get_collection(cls.collection_name)
        return await collection.delete_one(query)


if __name__ == "__main__":
    import asyncio
    asyncio.run(initialize_database())
