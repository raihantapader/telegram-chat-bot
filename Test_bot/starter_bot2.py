import os
import sys
import uuid
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime

load_dotenv()

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

Telegram_Bot_Token = os.getenv("STARTER_BOT_TOKEN")

# MongoDB connection
MongoDB_Url = os.getenv("MONGODB_URI")
mongo_client = MongoClient(MongoDB_Url)
db = mongo_client['Raihan']
test_collection = db['active_test_ids']

# Bot configurations
CUSTOMER_BOTS = [
    {"name": "🤖 Bot_1 - Ted", "username": "Cust0m3rBot"},
    {"name": "🤖 Bot_2 - James", "username": "Cust0m4rBot"},
    {"name": "🤖 Bot_3 - Charlie", "username": "Cust0m5rBot"},
    {"name": "🤖 Bot_4 - Jayson", "username": "Cust0m6rBot"},
    {"name": "🤖 Bot_5 - Peter", "username": "Cust0m7rBot"}
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Generate a unique Test ID
    test_id = str(uuid.uuid4().hex[:6]).upper()  
    chat_id = update.message.chat.id

    # Store test_id in database as "active" test
    test_data = {
        "test_id": test_id,
        "status": "active",
        "created_at": datetime.now(),
        "created_by": chat_id
    }
    
    # Insert into database
    test_collection.insert_one(test_data)
    
    print(f"✅ Generated Test ID: {test_id}")

    # Create clickable bot links that show as commands
    bot_links = ""
    for bot in CUSTOMER_BOTS:
        deep_link = f"https://t.me/{bot['username']}?start={test_id}"
        bot_links += f"• [/start {bot['name']}]({deep_link})\n"

    message = (
        f"✅ *Reply Speed Test Created!*\n\n"
        f"*Test ID:* `{test_id}`\n\n"
        f"📌 This Test ID has been saved to the database.\n\n"
        f"👍 Click any bot below to start:\n"
        f"{bot_links}\n"
        f"Each bot will automatically use Test ID: `{test_id}`\n\n"
        f"👉 *Instructions:*\n"
        f"1️⃣ Click on any `/start Bot X` command above\n"
        f"2️⃣ The bot will open and start automatically\n"
        f"3️⃣ Reply as fast as you can. The bots will handle the timing.\n\n"
        f"Later, we can centralize stats from all bots using this Test ID.\n\n"
        f"Happy testing . . . 🚀"
    )

    await update.message.reply_text(message, parse_mode="Markdown", disable_web_page_preview=True)

def main():
    _bot_application = ApplicationBuilder().token(Telegram_Bot_Token).build()
    _bot_application.add_handler(CommandHandler('start', start))
    
    print("="*70)
    print("STARTER BOT IS RUNNING".center(70))
    print("="*70)
    print("\nWaiting for /start command to create Test ID...\n")
    
    _bot_application.run_polling(drop_pending_updates=True, poll_interval=1)

if __name__ == '__main__':
    main()
