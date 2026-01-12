from __future__ import annotations
import os
from datetime import datetime, timezone
from typing import List, Dict, Optional

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.environ["MONGODB_URI"]
MONGODB_DB = os.environ.get["MONGODB_DB"]

client = AsyncIOMotorClient(MONGODB_URI)
db = client[MONGODB_DB]

tests_col = db["tests"]
messages_col = db["messages"]
participants_col = db["participants"]  # maps (chat_id, bot_id) -> test_id


def now_utc():
    return datetime.now(timezone.utc)


async def ensure_indexes():
    await tests_col.create_index("created_at")
    await messages_col.create_index([("test_id", 1), ("bot_id", 1), ("ts", 1)])
    await participants_col.create_index([("chat_id", 1), ("bot_id", 1)], unique=True)


async def create_test(test_id: str, created_by_user_id: int) -> None:
    await tests_col.insert_one(
        {
            "_id": test_id,
            "created_at": now_utc(),
            "created_by": created_by_user_id,
            "status": "active",
        }
    )


async def test_exists(test_id: str) -> bool:
    doc = await tests_col.find_one({"_id": test_id}, {"_id": 1})
    return doc is not None


async def upsert_participant(chat_id: int, bot_id: str, test_id: str) -> None:
    await participants_col.update_one(
        {"chat_id": chat_id, "bot_id": bot_id},
        {"$set": {"test_id": test_id, "updated_at": now_utc()}, "$setOnInsert": {"created_at": now_utc()}},
        upsert=True,
    )


async def get_participant_test_id(chat_id: int, bot_id: str) -> Optional[str]:
    doc = await participants_col.find_one({"chat_id": chat_id, "bot_id": bot_id}, {"test_id": 1})
    return doc.get("test_id") if doc else None


async def insert_message(test_id: str, bot_id: str, role: str, text: str, chat_id: int) -> None:
    # role: "salesperson" or "customer"
    await messages_col.insert_one(
        {
            "test_id": test_id,
            "bot_id": bot_id,
            "chat_id": chat_id,
            "role": role,
            "text": text,
            "ts": now_utc(),
        }
    )


async def get_last_messages(test_id: str, bot_id: str, limit: int = 10) -> List[Dict]:
    cursor = (
        messages_col.find({"test_id": test_id, "bot_id": bot_id})
        .sort("ts", -1)
        .limit(limit)
    )
    docs = await cursor.to_list(length=limit)
    docs.reverse()  # oldest -> newest
    return docs
