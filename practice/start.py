import os
import uuid
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Initialize the storage for Test IDs
test_id_storage = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    test_id = str(uuid.uuid4().hex[:6]).upper()  # Generate a 6-character Test ID
    test_id_storage[test_id] = {"starter_bot": update.message.chat.id, "customer_bots": []}

    await update.message.reply_text(
        f"TestID: {test_id} has been generated for you. Use this ID in other customer bots to start the conversation with Sales Bot."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/start - Start the conversation with a unique TestID.")

# Start the bot
def start_starter_bot():
    application = ApplicationBuilder().token(os.getenv("STARTER_BOT_TOKEN")).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.run_polling()

if __name__ == "__main__":
    start_starter_bot()
