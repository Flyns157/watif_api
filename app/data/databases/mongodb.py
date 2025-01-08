from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from fastapi import HTTPException, status
from datetime import datetime, date

from ...utils.config.modes import Mode
from ...utils.config import Settings
from ...utils import generate_uuid
from ..models import Role, UserModel
from ... import main_logger


MONGODB_URI = Settings.MONGODB_URI
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
                connection_url = f"mongodb://{MONGODB_USER}:{MONGODB_PASSWORD}@{MONGODB_URI}/{MONGODB_DB_NAME}?authSource=admin"
            else:
                connection_url = f"mongodb://{MONGODB_URI}"

            # Connect to MongoDB
            self.client = AsyncIOMotorClient(connection_url)
            
            # Test the connection
            await self.client.admin.command('ping')
            
            self.db = self.client[MONGODB_DB_NAME]
            
            # Initialize database structure
            if Settings.MODE == Mode.MAIN:
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
                Role(
                    name="admin" , 
                    rights=[
                        "*", 
                        "users:create:all", 
                        "users:read:all", 
                        "users:update:all", 
                        "users:delete:all", 
                        "threads:read:public:all",
                    ], inherits=["user"]
                ).model_dump()
            )
            main_logger.info("Default admin role created successfully")

        existing_role = await self.db.roles.find_one({"name": "user"})
        if existing_role is None:
            self.db.roles.insert_one(
                Role(
                    name="user", 
                    rights=[
                        "users:update:own", 
                        "users:delete:own",
                        "posts:create:own",
                        "posts:read:all",
                        "posts:update:own",
                        "posts:delete:own",
                        "comments:create:own",
                        "comments:read:all",
                        "comments:update:own",
                        "comments:delete:own",
                        "likes:create:own",
                        "likes:delete:own",
                        "dislikes:create:own",
                        "dislikes:read:all",
                        "dislikes:delete:own",
                        "threads:create:own",
                        "threads:read:public:all",
                        "threads:update:own",
                        "threads:delete:own",
                        "interests:create:own",
                        "interests:read:all",
                        "interests:update:own",
                        "interests:delete:own",
                        "keys:create:own",
                        "keys:read:all",
                    ]
                ).model_dump()
            )
            main_logger.info("Default user role created successfully")

        # Create default a default admin if it doesn't exist
        existing_user = await self.db.users.find_one({"username": "admin"})
        if existing_user is None:
            from ...security.auth import get_password_hash
            self.db.users.insert_one(
                UserModel(
                    uuid = generate_uuid(),
                    role = "admin",
                    username = "admin",
                    hashed_password = get_password_hash(Settings.ADMIN_PASSWORD),
                    email = Settings.ADMIN_EMAIL,
                    name = "Admin",
                    surname = "Admin",
                    pp = r"pp/default-avatar-icon-of-social-media-user-vector.jpg",
                    birth_date = date.today(),
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
