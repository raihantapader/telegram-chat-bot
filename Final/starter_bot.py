import asyncio
import os
import uuid
import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv

# Load environment variables (API keys)
load_dotenv()
Telegram_Bot_Token = os.getenv("STARTER_BOT_TOKEN")
OPEPNAI_API_KEY = os.getenv("aluraagency_OPEPNAI_API_KEY")
openai.api_key = OPEPNAI_API_KEY

conversation_memory = {}  

# Function to start the conversation and generate a unique Test 
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Generate a unique Test ID (e.g., FJF2TD)
    test_id = str(uuid.uuid4().hex[:6]).upper()  # Generate a 6-character Test ID
    conversation_memory[test_id] = []  # Initialize conversation history for this Test ID

    # Get the bot's username (which bot is sending the command)
    bot_username = update.message.chat.username

    # Create the clickable Test ID link for the user (other bots will also get this ID)
    test_id_link = f"https://t.me/{bot_username}?start={test_id}"

    # Send a message with the unique Test ID and instructions
    await update.message.reply_text(
        f"✅ *Reply Speed Test Created!* \n\n"
        f"Test ID: `{test_id}`\n\n"
       # f"Test ID: [{test_id}]({test_id_link})\n\n"
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
    , parse_mode="Markdown" )
 
# Handle incoming message and generate responses using the GPT model
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text 
    
    # Get the Test ID from the message (if /start was used)
    if update.message.text.startswith('/newtest'):
        test_id = update.message.text.split(" ")[1]
        if test_id not in conversation_memory:
            await update.message.reply_text(f"Invalid TestID. Please use a valid TestID.")
            return
        await update.message.reply_text(f"TestID {test_id} is confirmed. Start chatting.")

    else:
        test_id = update.message.chat.id  # Use Telegram chat ID as the TestID temporarily
        if test_id not in conversation_memory:
            await update.message.reply_text(
            f"Hey!  I'm the Reply Test Starter Bot.\n\n"
            f"Use /newtest to create a new reply test conversation.")
            return

       
# Initialize the bot application
def main():

    _bot_application = ApplicationBuilder().token(Telegram_Bot_Token).build()

    _bot_application.add_handler(CommandHandler('newtest', start))
    _bot_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot polling started...")
    _bot_application.run_polling(drop_pending_updates=True, poll_interval=1)

if __name__ == '__main__':
    main()
