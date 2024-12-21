import motor.motor_asyncio

from ..utils.config import Settings


# Set up the MongoDB connection
client = motor.motor_asyncio.AsyncIOMotorClient(Settings.MONGODB_URI)
client.uuid_representation = 5
db = client[Settings.MONGODB_DATABASE]


# User collection
user_collection = db.get_collection("users")

user_collection.create_index("uuid", unique=True)
user_collection.create_index("username", unique=True)
user_collection.create_index("email", unique=True)
