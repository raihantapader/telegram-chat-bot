# telegram_chat.py
# Monitor ALL private chats automatically
# Only stores REAL PERSON messages - ALL bots are blocked

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient, errors
import os
import sys
import asyncio

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

load_dotenv()

# Telegram API credentials
API_ID = int(os.getenv("My_app_api_id"))
API_HASH = os.getenv("My_app_api_hash")
PHONE = os.getenv("My_telegram_phone", "").replace(" ", "")
SESSION_STRING = os.getenv("TELEGRAM_SESSION")

# MongoDB connection
MongoDB_Url = os.getenv("DB_URI")
mongo_client = MongoClient(MongoDB_Url)
db = mongo_client['Raihan']
chat_collection = db['telegram_chats']
friends_collection = db['telegram_friends']

# SESSION HANDLING
if SESSION_STRING:
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    SESSION_EXISTS = True
else:
    client = TelegramClient('my_session', API_ID, API_HASH)
    SESSION_EXISTS = False

MY_USER_ID = None

# Duplicate prevention
processed_ids = set()
process_lock = asyncio.Lock()

# Cache for friend person_ids (chat_id -> person_id)
friend_cache = {}


def get_or_create_person_id(chat_id: int, username: str, friend_name: str) -> int:
    """Get existing person_id or create new one for a friend"""
    
    if chat_id in friend_cache:
        return friend_cache[chat_id]
    
    friend = friends_collection.find_one({"chat_id": chat_id})
    
    if friend:
        person_id = friend["person_id"]
        
        updates = {}
        if username and friend.get("username") != username:
            updates["username"] = username
        if friend_name and friend.get("name") != friend_name:
            updates["name"] = friend_name
        
        if updates:
            friends_collection.update_one(
                {"chat_id": chat_id},
                {"$set": updates}
            )
    else:
        last_friend = friends_collection.find_one(sort=[("person_id", -1)])
        person_id = (last_friend["person_id"] + 1) if last_friend else 1
        
        friends_collection.insert_one({
            "person_id": person_id,
            "username": username or "no_username",
            "chat_id": chat_id,
            "name": friend_name or "Unknown",
            "created_at": datetime.now()
        })
        print(f"🆕 New friend added: {friend_name} (@{username or 'no_username'}) → Person {person_id}")
    
    friend_cache[chat_id] = person_id
    return person_id


def cleanup_database():
    """Remove ONLY duplicates, keep all unique messages"""
    print("\n🧹 Cleaning duplicates...")
    
    removed = 0
    
    pipeline1 = [
        {"$match": {"message_id": {"$exists": True}}},
        {"$group": {
            "_id": {"message_id": "$message_id", "chat_id": "$chat_id"},
            "docs": {"$push": "$_id"},
            "count": {"$sum": 1}
        }},
        {"$match": {"count": {"$gt": 1}}}
    ]
    
    for doc in chat_collection.aggregate(pipeline1):
        ids_to_delete = doc['docs'][1:]
        result = chat_collection.delete_many({"_id": {"$in": ids_to_delete}})
        removed += result.deleted_count
    
    pipeline2 = [
        {"$match": {"message_id": {"$exists": False}}},
        {"$group": {
            "_id": {
                "chat_id": "$chat_id",
                "role": "$role",
                "name": "$name",
                "text": "$text"
            },
            "docs": {"$push": "$_id"},
            "count": {"$sum": 1}
        }},
        {"$match": {"count": {"$gt": 1}}}
    ]
    
    for doc in chat_collection.aggregate(pipeline2):
        ids_to_delete = doc['docs'][1:]
        result = chat_collection.delete_many({"_id": {"$in": ids_to_delete}})
        removed += result.deleted_count
    
    try:
        chat_collection.create_index(
            [("message_id", 1), ("chat_id", 1)],
            unique=True,
            sparse=True,
            name="unique_message_idx"
        )
    except errors.OperationFailure:
        pass
    
    total = chat_collection.count_documents({})
    friends_count = friends_collection.count_documents({})
    
    if removed > 0:
        print(f"   ✅ Removed {removed} duplicates")
    else:
        print(f"   ✅ No duplicates found")
    
    print(f"   📊 Total messages: {total}")
    print(f"   👥 Total friends: {friends_count}\n")


def load_friends_cache():
    """Load existing friends into cache"""
    print("👥 Loading friends...")
    for friend in friends_collection.find():
        friend_cache[friend["chat_id"]] = friend["person_id"]
        print(f"   Person {friend['person_id']}: {friend['name']} (@{friend.get('username', 'no_username')})")
    
    if not friend_cache:
        print("   No friends yet. They will be added automatically when they message you.")
    print()


async def insert_message(person_id: int, message_id: int, chat_id: int, role: str, name: str, text: str):
    """Store message in MongoDB with duplicate prevention"""
    
    async with process_lock:
        if message_id in processed_ids:
            return False
        processed_ids.add(message_id)
    
    message = {
        "person_id": person_id,
        "message_id": message_id,
        "chat_id": chat_id,
        "role": role,
        "name": name,
        "text": text,
        "timestamp": datetime.now()
    }
    
    try:
        chat_collection.insert_one(message)
        icon = "📤" if role == "sender" else "📥"
        print(f"{icon} [Person {person_id}] [{role}] {name}: {text[:50]}{'...' if len(text) > 50 else ''}")
        return True
    except errors.DuplicateKeyError:
        return False
    except Exception as e:
        print(f"⚠️ DB Error: {e}")
        return False


@client.on(events.NewMessage)
async def handle_new_message(event):
    """Handle messages from ALL private chats (only real people)"""
    global MY_USER_ID
    
    message_id = event.message.id
    
    if message_id in processed_ids:
        return
    
    text = event.message.text
    if not text:
        return
    
    # Only process private chats (not groups/channels)
    if not event.is_private:
        return
    
    chat = await event.get_chat()
    chat_id = event.chat_id
    
    # Skip if it's yourself (saved messages)
    if chat_id == MY_USER_ID:
        return

    # BLOCK ALL BOTS - Only allow real people
  
    # Check 1: Telegram's bot flag
    if getattr(chat, 'bot', False):
        return
    
    # Check 2: Username ends with 'bot' (case insensitive)
    username = getattr(chat, 'username', None)
    if username and username.lower().endswith(('bot', 'Bot')):
        return
    
    # Get friend's username and name
    chat_username = getattr(chat, 'username', None)
    friend_first = getattr(chat, 'first_name', '') or ''
    friend_last = getattr(chat, 'last_name', '') or ''
    friend_name = f"{friend_first} {friend_last}".strip() or "Unknown"
    
    # Get or create person_id for this friend (automatic!)
    person_id = get_or_create_person_id(chat_id, chat_username, friend_name)
    
    sender = await event.get_sender()
    sender_id = sender.id if sender else 0
    
    if sender:
        first = getattr(sender, 'first_name', '') or ''
        last = getattr(sender, 'last_name', '') or ''
        name = f"{first} {last}".strip() or "Unknown"
    else:
        name = "Unknown"
    
    role = "receiver" if sender_id == MY_USER_ID else "sender"
    
    await insert_message(
        person_id=person_id,
        message_id=message_id,
        chat_id=chat_id,
        role=role,
        name=name,
        text=text
    )


async def main():
    global MY_USER_ID
    
    print("=" * 50)
    print("TELEGRAM AUTO CHAT MONITOR".center(50))
    print("=" * 50)
    
    # Check session status
    if SESSION_EXISTS:
        print("\n🔑 Using saved session (No OTP needed)")
    else:
        print("\n⚠️ No session found!")
        print("   Please run my_session.py first to generate TELEGRAM_SESSION")
        print("   Then add it to your .env file")
        print("=" * 50)
        return
    
    print("🤖 Bot Filter: ON (All bots blocked)")
    
    # Run cleanup on startup
    cleanup_database()
    
    # Load existing friends
    load_friends_cache()
    
    # CONNECT WITHOUT ASKING FOR OTP
    try:
        await client.connect()
        
        if not await client.is_user_authorized():
            print("\n❌ Session expired or invalid!")
            print("   Please run my_session.py again to generate new TELEGRAM_SESSION")
            print("=" * 50)
            return
        
        me = await client.get_me()
        MY_USER_ID = me.id
        
        print(f"✅ Logged in: {me.first_name} {me.last_name or ''}")
        print(f"🆔 My ID: {MY_USER_ID}")
        print(f"🎯 Monitoring: REAL PEOPLE ONLY (bots ignored)")
        print(f"💾 Database: telegram_chats")
        print("=" * 50)
        print("\n📡 Listening for messages from real people...\n")
        
        await client.run_until_disconnected()
        
    except Exception as e:
        print(f"\n❌ Connection Error: {e}")
        print("   Please check your internet connection or run my_session.py again")
        print("=" * 50)


if __name__ == '__main__':
    asyncio.run(main())