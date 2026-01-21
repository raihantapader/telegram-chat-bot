# my_session.py
# Run this ONCE to generate session string
# After running, copy the session string to your .env file

from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv
import os

load_dotenv()

API_ID = int(os.getenv("My_app_api_id"))
API_HASH = os.getenv("My_app_api_hash")
PHONE = os.getenv("My_telegram_phone", "").replace(" ", "")

print("="*50)
print("TELEGRAM SESSION GENERATOR".center(50))
print("="*50)
print("\nThis will generate a session string.")
print("You only need to run this ONCE.\n")

with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    # This will ask for phone, code, and password (if 2FA enabled)
    session_string = client.session.save()
    
    print("\n" + "="*50)
    print("✅ SESSION STRING GENERATED!")
    print("="*50)
    print("\nCopy this string and add to your .env file:")
    print("\nTELEGRAM_SESSION=" + session_string)
    print("\n" + "="*50)
    print("\nNow you can run telegram_chat_monitor.py")
    print("="*50)