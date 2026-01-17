import asyncio
from doctest import testmod
import os
import uuid
from arrow import get
from telegram.ext import filters
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime


load_dotenv()

Telegram_Bot_Token = os.getenv("STARTER_BOT_TOKEN")
OPEPNAI_API_KEY = os.getenv("aluraagency_OPEPNAI_API_KEY")

MongoDB_Url = os.getenv("MONGODB_URI")
client = MongoClient(MongoDB_Url)
db = client['Raihan']
test_collection = db['Test_ID']

# Function to insert a test_id into the MongoDB collection
def insert_test_id(test_id, chat_id):
    test_data = {
        "test_id": test_id,
        "chat_id": chat_id,
        "timestamp": datetime.now()
    }
    
    test_collection.insert_one(test_data)

# Function to retrieve the test_id from the database based on chat_id
def get_test_id(chat_id):
    test_data = test_collection.find_one({"chat_id": chat_id})
    if test_data:
        return test_data['test_id']
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    test_id = str(uuid.uuid4().hex[:6]).upper()  
    chat_id = update.message.chat.id
    
    # Store the test_id in MongoDB
    insert_test_id(test_id, chat_id)
    
    bot_username = update.message.chat.username
    test_id_link = f"https://t.me/{bot_username}?start={test_id}"
    
    print(f"Generated Test ID: {test_id}")

    await update.message.reply_text(
        f"✅ *Reply Speed Test Created!* \n\n"
        f"Test ID: `{test_id}`\n\n"
        f"Use this ID with the other bots so they all log the same session.\n\n"
        f"👉 Next steps:\n"
        f"1️⃣ Open each customer bot:\n\n"
        f"• @Cust0m7rBot\n"
        f"• @Cust0m6rBot\n"
        f"• @Cust0m5rBot\n"
        f"• @Cust0m4rBot\n"
        f"• @Cust0m3rBot\n\n"
        f"2️⃣ In each bot, send: [/start {test_id}]({test_id_link})\n\n"
        f"3️⃣ Then reply as fast as you can. The bots will handle the timing.\n\n"
        f"Later, we can centralize stats from all bots using this TestID.\n\n"
        f"Happy testing . . . 🚀"
    , parse_mode="Markdown")

# Function to handle incoming messages (not needed for this specific request but kept for reference)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    chat_id = update.message.chat.id
    
    # Retrieve test_id from MongoDB using chat_id
    test_id = get_test_id(chat_id)
    if not test_id:
        await update.message.reply_text(
            f"Hey! I'm the Reply Test Starter Bot.\n\n"
            f"Use /newtest to create a new reply test conversation."
        )
        return

def main():
    _bot_application = ApplicationBuilder().token(Telegram_Bot_Token).build()

    # Add command handlers
    _bot_application.add_handler(CommandHandler('start', start))  # Start command to initiate the test
    _bot_application.add_handler(CommandHandler('newtest', start))  # Alias for new test command
    _bot_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot polling started...")
    _bot_application.run_polling(drop_pending_updates=True, poll_interval=1)
    
   # print("Test id:", get_test_id)
    
if __name__ == '__main__':
    main()
   