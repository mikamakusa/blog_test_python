from motor.motor_asyncio import AsyncIOMotorClient
from config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    dbs = {}

db = Database()

async def connect_to_mongo():
    try:
        connection_string = f"mongodb://{settings.mongodb_username}:{settings.mongodb_password}@{settings.mongodb_host}:{settings.mongodb_port}"
        db.client = AsyncIOMotorClient(connection_string)
        # Connect to all relevant databases
        db.dbs = {
            'users': db.client[settings.users_db],
            'posts': db.client[settings.posts_db],
            'ads': db.client[settings.ads_db],
            'events': db.client[settings.events_db],
            'polls': db.client[settings.polls_db],
        }
        logger.info("Connected to MongoDB for metrics.")
    except Exception as e:
        logger.error(f"Could not connect to MongoDB: {e}")
        raise e

async def close_mongo_connection():
    if db.client:
        db.client.close()
        logger.info("Closed MongoDB connection.")

def get_collection(service: str):
    """Get collection from the correct database."""
    collections = {
        'users': settings.users_collection,
        'posts': settings.posts_collection,
        'ads': settings.ads_collection,
        'events': settings.events_collection,
        'polls': settings.polls_collection,
    }
    return db.dbs[service][collections[service]] 