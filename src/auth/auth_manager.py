import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List
from src.database.database import get_db


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def generate_token() -> str:
    return secrets.token_urlsafe(32)


async def admin_exists() -> bool:
    db = get_db()
    admin = await db.admins.find_one({})
    return admin is not None


async def register_admin(username: str, password: str) -> Dict:
    db = get_db()

    if await admin_exists():
        raise ValueError("Admin already registered")

    admin_data = {
        "username": username,
        "password": hash_password(password),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    result = await db.admins.insert_one(admin_data)
    if not result.acknowledged:
        raise Exception("Failed to register admin")
    return {"username": username, "created_at": admin_data["created_at"]}


async def authenticate_admin(username: str, password: str) -> bool:
    db = get_db()
    admin = await db.admins.find_one({"username": username})

    if not admin:
        return False

    password_hash = hash_password(password)
    return admin["password"] == password_hash


async def create_api_token(name: str, description: Optional[str] = None,
                           expires_in_days: Optional[int] = None) -> Dict:
    db = get_db()

    token = generate_token()
    created_at = datetime.now(timezone.utc)
    expires_at = None

    if expires_in_days:
        expires_at = created_at + timedelta(days=expires_in_days)

    token_data = {
        "token": token,
        "name": name,
        "description": description,
        "created_at": created_at.isoformat(),
        "expires_at": expires_at.isoformat() if expires_at else None,
        "is_active": True,
        "last_used": None,
    }

    await db.api_tokens.insert_one(token_data)

    return {
        "token": token,
        "name": name,
        "description": description,
        "created_at": token_data["created_at"],
        "expires_at": token_data["expires_at"],
        "is_active": True,
    }


async def verify_token(token: str) -> bool:
    db = get_db()

    token_data = await db.api_tokens.find_one({"token": token, "is_active": True})

    if not token_data:
        return False

    if token_data.get("expires_at"):
        expires_at = datetime.fromisoformat(token_data["expires_at"])
        if datetime.now(timezone.utc) > expires_at:
            return False

    await db.api_tokens.update_one(
        {"token": token},
        {"$set": {"last_used": datetime.now(timezone.utc).isoformat()}}
    )

    return True


async def list_tokens() -> List[Dict]:
    db = get_db()

    tokens = []
    async for token_data in db.api_tokens.find({}).sort("created_at", -1):
        tokens.append({
            "name": token_data["name"],
            "description": token_data.get("description"),
            "token_preview": token_data["token"][:8] + "..." if token_data["token"] else "",
            "created_at": token_data["created_at"],
            "expires_at": token_data.get("expires_at"),
            "is_active": token_data["is_active"],
            "last_used": token_data.get("last_used"),
        })

    return tokens


async def revoke_token(token_name: str) -> bool:
    db = get_db()

    result = await db.api_tokens.update_one(
        {"name": token_name},
        {"$set": {"is_active": False}}
    )

    return result.modified_count > 0


async def delete_token(token_name: str) -> bool:
    db = get_db()

    result = await db.api_tokens.delete_one({"name": token_name})
    return result.deleted_count > 0

