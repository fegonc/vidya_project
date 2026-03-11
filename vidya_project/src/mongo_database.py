from motor.motor_asyncio import AsyncIOMotorClient

from vidya_project.src.settings import Settings

settings = Settings()

# Cliente MongoDB
mongo_client = AsyncIOMotorClient(settings.MONGO_URL)
mongo_db = mongo_client[settings.MONGO_DB_NAME]

# Collection específica para comentários de vendas
comments_collection = mongo_db["sale_comments"]

def get_mongo_db():
    """Dependency para injetar o banco MongoDB"""
    return mongo_db

async def get_comments_collection():
    """Dependency para injetar a collection de comentários"""
    return comments_collection