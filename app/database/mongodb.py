from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from fastapi import HTTPException, status
from datetime import datetime, date

from ..utils.config import Settings
from ..utils import generate_uuid
from ..models import Role, User
from .. import main_logger


MONGODB_URL = Settings.MONGODB_URI
MONGODB_USER = Settings.MONGODB_USER
MONGODB_PASSWORD = Settings.MONGODB_PASSWORD
MONGODB_DB_NAME = Settings.MONGODB_DATABASE


class MongoManager:
    client: AsyncIOMotorClient | None = None
    db: AsyncIOMotorDatabase | None = None

    async def connect_to_database(self):
        try:
            # Create connection URL with authentication
            if MONGODB_USER and MONGODB_PASSWORD:
                connection_url = f"mongodb://{MONGODB_USER}:{MONGODB_PASSWORD}@localhost:27017/{MONGODB_DB_NAME}?authSource=admin"
            else:
                connection_url = MONGODB_URL

            # Connect to MongoDB
            self.client = AsyncIOMotorClient(connection_url)
            
            # Test the connection
            await self.client.admin.command('ping')
            
            self.db = self.client[MONGODB_DB_NAME]
            
            # Initialize database structure
            try:
                await self.initialize_database()
            except Exception as e:
                main_logger.info(f"Error creating indexes: {e}")
                # Don't raise the error as indexes might already exist
                
        except Exception as e:
            main_logger.info(f"Could not connect to MongoDB: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not connect to database"
            )


    async def initialize_database(self):
        self.client.uuid_representation = 5

        # Create indexes
        await self.db.users.create_index("uuid", unique=True)
        await self.db.users.create_index("username", unique=True)
        await self.db.users.create_index("email", unique=True)

        await self.db.roles.create_index("name", unique=True)
        main_logger.info("Indexes created successfully")

        # Create default roles if they don't exist
        existing_role = await self.db.roles.find_one({"name": "admin"})
        if existing_role is None:
            self.db.roles.insert_one(
                Role(name="admin" , rights=["*", "create:all", "read:all", "update:all", "delete:all", ], inherits=["user"]).model_dump()
            )
            main_logger.info("Default admin role created successfully")

        existing_role = await self.db.roles.find_one({"name": "user"})
        if existing_role is None:
            self.db.roles.insert_one(
                Role(name="user" , rights=["update:self", "delete:self"]).model_dump()
            )
            main_logger.info("Default user role created successfully")

        # Create default a default admin if it doesn't exist
        existing_user = await self.db.users.find_one({"username": "admin"})
        if existing_user is None:
            from ..auth import get_password_hash
            self.db.users.insert_one(
                User(
                    uuid = generate_uuid(),
                    role = "admin",
                    username = "admin",
                    hashed_password = get_password_hash(Settings.ADMIN_PASSWORD),
                    email = Settings.ADMIN_EMAIL,
                    name = "Admin",
                    surname = "Admin",
                    pp = r"images/pp/default-avatar-icon-of-social-media-user-vector.jpg",
                    birth_date = str(date.today()),
                    followed = [],
                    blocked = [],
                    interests = [],
                    description = "",
                    disabled = False,
                    created_at = datetime.now(),
                    updated_at = datetime.now()
                ).model_dump()
            )
            main_logger.info("Default admin user created successfully")


    async def close_database_connection(self):
        if self.client is not None:
            self.client.close()
