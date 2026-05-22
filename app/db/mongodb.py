# app/db/mongodb.py
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

    @classmethod
    def connect_db(cls):
        cls.client = AsyncIOMotorClient(settings.MONGODB_URI)
        try:
            cls.db = cls.client.get_default_database()
        except Exception:
            cls.db = cls.client["chatbot_db"]

    @classmethod
    def close_db(cls):
        if cls.client:
            cls.client.close()

db = MongoDB()
