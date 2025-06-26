from motor.motor_asyncio import AsyncIOMotorClient
from config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    database = None

db = Database()

async def connect_to_mongo():
    """Create database connection."""
    try:
        connection_string = f"mongodb://{settings.mongodb_username}:{settings.mongodb_password}@{settings.mongodb_host}:{settings.mongodb_port}"
        db.client = AsyncIOMotorClient(connection_string)
        db.database = db.client[settings.mongodb_database]
        logger.info("Connected to MongoDB.")
    except Exception as e:
        logger.error(f"Could not connect to MongoDB: {e}")
        raise e

async def close_mongo_connection():
    """Close database connection."""
    if db.client:
        db.client.close()
        logger.info("Closed MongoDB connection.")

def get_collection(collection_name: str):
    """Get collection from database."""
    return db.database[collection_name] 