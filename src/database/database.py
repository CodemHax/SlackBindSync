from motor.motor_asyncio import AsyncIOMotorClient

client = None
db = None

async def init_db(mongo_uri, mongo_db):
    global client, db
    try:
        client = AsyncIOMotorClient(mongo_uri)
        await client.admin.command('ping')
        db = client[mongo_db]
        return db
    except Exception as e:
        raise

def get_db():
    return db

def get_client():
    return client

