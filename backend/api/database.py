import motor.motor_asyncio
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client.ai_asset_memory

def get_db():
    return db

async def init_db():
    # Example initialization: create unique indexes if needed
    await db.users.create_index("email", unique=True)
    await db.users.create_index("username", unique=True)
