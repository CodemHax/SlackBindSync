import time
import uuid
from src.database.database import get_db

def api_shape(d):
    if not d:
        return None
    d = dict(d)
    d["id"] = str(d.pop("_id"))
    return d


async def configure():
    db = get_db()
    col = db["messages"]
    await col.create_index("timestamp")
    await col.create_index("tg_msg_id", sparse=True)
    await col.create_index("dc_msg_id", sparse=True)


async def add_message(source, text, username=None, tg_msg_id=None, dc_msg_id=None, reply_to_tg_id=None, reply_to_dc_id=None, reply_to_id=None,timestamp=None):
    db = get_db()
    col = db["messages"]
    doc = {
        "_id": str(uuid.uuid4()),
        "source": source,
        "text": text,
        "username": username,
        "timestamp": float(timestamp or time.time()),
        "tg_msg_id": tg_msg_id,
        "dc_msg_id": dc_msg_id,
        "reply_to_id": reply_to_id,
        "reply_to_tg_id": reply_to_tg_id,
        "reply_to_dc_id": reply_to_dc_id,
    }
    await col.insert_one(doc)
    return doc["_id"]


async def list_messages(limit=50, offset=0):
    db = get_db()
    col = db["messages"]
    cursor = col.find({}, sort=[("timestamp", -1)], skip=offset)
    items = await cursor.to_list(length=limit)
    return [api_shape(d) for d in items]


async def get_message(internal_id):
    db = get_db()
    col = db["messages"]
    d = await col.find_one({"_id": internal_id})
    return api_shape(d)


async def find_by_tg_id(tg_msg_id):
    db = get_db()
    col = db["messages"]
    d = await col.find_one({"tg_msg_id": tg_msg_id})
    return api_shape(d)


async def find_by_dc_id(dc_msg_id):
    db = get_db()
    col = db["messages"]
    d = await col.find_one({"dc_msg_id": dc_msg_id})
    return api_shape(d)


async def set_dc_id_for_tg(tg_msg_id, dc_msg_id):
    db = get_db()
    col = db["messages"]
    await col.update_many({"tg_msg_id": tg_msg_id}, {"$set": {"dc_msg_id": dc_msg_id}})


async def set_tg_id_for_dc(dc_msg_id, tg_msg_id):
    db = get_db()
    col = db["messages"]
    await col.update_many({"dc_msg_id": dc_msg_id}, {"$set": {"tg_msg_id": tg_msg_id}})


async def set_tg_msg_id(internal_id, tg_msg_id):
    db = get_db()
    col = db["messages"]
    await col.update_one({"_id": internal_id}, {"$set": {"tg_msg_id": tg_msg_id}})


async def set_dc_msg_id(internal_id, dc_msg_id):
    db = get_db()
    col = db["messages"]
    await col.update_one({"_id": internal_id}, {"$set": {"dc_msg_id": dc_msg_id}})
