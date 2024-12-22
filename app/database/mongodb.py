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

if __name__ == "__main__":
    import asyncio
    asyncio.run(initialize_database())
