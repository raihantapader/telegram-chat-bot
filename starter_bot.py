import random
import string
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

customer_bot_tokens = [
    "TELEGRAM_BOT_1_TOKEN", 
    "TELEGRAM_BOT_2_TOKEN",
    "TELEGRAM_BOT_3_TOKEN",
    "TELEGRAM_BOT_4_TOKEN",
    "TELEGRAM_BOT_5_TOKEN"
]

# Command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! Welcome to the Bot. \n Please write /start to start the conversation.")

async def other_bot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(""" Other Bots:
   
    /linkedin - To get the LinkedIn profile URL
    /facebook - To get Facebook profile URL """)

# Command responses
async def linkedin_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("LinkedIn URL => https://www.linkedin.com/in/raihan-tapader06/")


async def facebook_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Facebook URL => https://www.facebook.com/raihantapader06/")

# Function to generate unique Test ID
async def generate_test_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# Command to create a new test and provide Test ID to all bots
async def new_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    test_id = await generate_test_id()

    # Send the Test ID to all customer bots via the Starter Bot
    for bot_token in customer_bot_tokens:
        # Send message to each customer bot with the Test ID
        bot = context.bot
        await bot.send_message(chat_id=bot_token, text=f"📝 Test ID: {test_id}\nUse this ID to log the same session with the VA Bot.")

    # Send the Test ID to the Starter Bot's chat
    await update.message.reply_text(f"""
    📝 Test ID: {test_id}
    Use this Test ID with other customer bots to log the same session.
    1️⃣ Open each customer bot
    2️⃣ In each bot, send: /start {test_id}
    3️⃣ Customer bots send queries to the VA Bot.
    """)

# Initialize the Starter Bot
def main():
    starter_bot_token = "STARTER_BOT_TOKEN"
    application = ApplicationBuilder().token(starter_bot_token).build()
    application.add_handler(CommandHandler("newtest", new_test))
    application.run_polling()

if __name__ == '__main__':
    main()
