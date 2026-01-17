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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Generate a unique Test ID
    test_id = str(uuid.uuid4().hex[:6]).upper()  
    chat_id = update.message.chat.id

    # Store test_id in database as "active" test
    test_data = {
        "test_id": test_id,
        "status": "active",
        "created_at": datetime.utcnow(),
        "created_by": chat_id
    }
    
    # Insert into database
    test_collection.insert_one(test_data)
    
    print(f"✅ Generated and stored Test ID: {test_id}")

    await update.message.reply_text(
        f"✅ *Reply Speed Test Created!* \n\n"
        f"Test ID: `{test_id}`\n\n"
        f"📌 This Test ID has been saved to the database.\n\n"
        f"🤖 Any customer bot that runs `/start` will automatically use this Test ID.\n\n"
        f"Use this ID with the other bots so they all log the same session.\n\n"
        f"👉 Next steps:\n"
        f"1️⃣ Open each customer bot:\n\n"
        f"• Customer Bot 1: @Cust0m3rBot\n"
        f"• Customer Bot 2: @Cust0m4rBot\n"
        f"• Customer Bot 3: @Cust0m5rBot\n"
        f"• Customer Bot 4: @Cust0m6rBot\n"
        f"• Customer Bot 5: @Cust0m7rBot\n\n"
        f"2️⃣💡 You can now start any of the 5 customer bots and they will use Test ID: `{test_id}`\n\n"
        f"3️⃣ Then reply as fast as you can. The bots will handle the timing.\n\n"
        f"Later, we can centralize stats from all bots using this TestID.\n\n"
        f"Happy testing . . . 🚀"
    , parse_mode="Markdown" )

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
