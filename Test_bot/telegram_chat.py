from telethon import TelegramClient, events
from telethon.sessions import StringSession
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
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

# MongoDB connection - use same as API
MongoDB_Url = os.getenv("DB_URI")
mongo_client = MongoClient(MongoDB_Url)
db = mongo_client['Raihan']
chat_collection = db['telegram_chats']

TARGET_USERNAME = os.getenv("friend_username")

# Create client
if SESSION_STRING:
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
else:
    client = TelegramClient('my_session', API_ID, API_HASH)

MY_USER_ID = None


def insert_message(chat_id: int, role: str, name: str, text: str):
    """Store message in MongoDB"""
    message = {
        "chat_id": chat_id,
        "role": role,
        "name": name,
        "text": text,
        "timestamp": datetime.now()
    }
    chat_collection.insert_one(message)
    
    icon = "📤" if role == "sender" else "📥"
    print(f"{icon} [{role}] {name}: {text[:50]}{'...' if len(text) > 50 else ''}")


@client.on(events.NewMessage)
async def handle_new_message(event):
    """Handle messages only from specific friend"""
    global MY_USER_ID
    
    text = event.message.text
    if not text:
        return
    
    chat = await event.get_chat()
    chat_username = getattr(chat, 'username', None)
    
    # Only process target friend's chat
    if chat_username != TARGET_USERNAME:
        return
    
    chat_id = event.chat_id
    
    sender = await event.get_sender()
    sender_id = sender.id if sender else 0
    
    if sender:
        first = getattr(sender, 'first_name', '') or ''
        last = getattr(sender, 'last_name', '') or ''
        name = f"{first} {last}".strip() or "Unknown"
    else:
        name = "Unknown"
    
    role = "sender" if sender_id == MY_USER_ID else "receiver"
    
    insert_message(chat_id=chat_id, role=role, name=name, text=text)


async def main():
    global MY_USER_ID
    
    print("="*50)
    print("TELEGRAM CHAT MONITOR".center(50))
    print("="*50)
    
    await client.start(phone=PHONE)
    
    me = await client.get_me()
    MY_USER_ID = me.id
    
    print(f"\n✅ Logged in: {me.first_name} {me.last_name or ''}")
    print(f"🆔 My ID: {MY_USER_ID}")
    print(f"🎯 Monitoring: @{TARGET_USERNAME}")
    print(f"💾 Database: telegram_chats")
    print("="*50)
    print("\n📡 Listening for messages...\n")
    
    await client.run_until_disconnected()


if __name__ == '__main__':
    asyncio.run(main())