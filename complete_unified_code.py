import os
import uuid
import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv

# Load environment variables (API keys)
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("STARTER_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

conversation_memory = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Generate a unique Test ID (e.g., FJF2TD)
    test_id = str(uuid.uuid4().hex[:6]).upper()  # Generate a 6-character Test ID
    conversation_memory[test_id] = []  # Initialize conversation history for this Test ID

    # Send a message with the unique Test ID and instructions
    await update.message.reply_text(
        f"Hey! I'm the Starter Bot. You have been assigned a unique TestID: @{test_id}\n\n"
        f"Use this ID with the other bots so they all log the same session.\n\n"
        f"👉 Next steps:\n"
        f"1️⃣ Open each bot:\n"
        f"• @Cust0m7rBot\n"
        f"• @Cust0m6rBot\n"
        f"• @Cust0m5rBot\n"
        f"• @Cust0m4rBot\n\n"
        f"2️⃣ In each bot, send: /start {test_id}\n"
        f"3️⃣ Then reply as fast as you can. The bots will handle the timing.\n\n"
        f"LATER, we can centralize stats from all bots using this Test ID.\n\n"
        f"Let me know if you need any help!"
    )

# Help command to show bot usage
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""
    Available Commands:
    /start - Start the conversation with a unique TestID.
    """)
    
async def other_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""
    Available Commands:
    /other - Show the other bots.
    """)
    
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""
    /help - Provides help.
    """)        

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text 
    
    # Get the Test ID from the message (if /start was used)
    if update.message.text.startswith('/start'):
        test_id = update.message.text.split(" ")[1]
        if test_id not in conversation_memory:
            await update.message.reply_text(f"Invalid TestID. Please use a valid ID.")
            return
        await update.message.reply_text(f"TestID {test_id} is confirmed. Start chatting!")

    else:
        # Respond using GPT-3 model for a sales assistant or customer bot
        test_id = update.message.chat.id  # Use Telegram chat ID as the TestID temporarily
        if test_id not in conversation_memory:
            await update.message.reply_text("Please type /start to initiate the conversation with a unique ID.")
            return

        # Here, you can call your GPT-3 or VA response function
        bot_response = await gpt_response(user_message, test_id)

        await update.message.reply_text(f"TestID: {test_id}\n{bot_response}")

# Function for getting GPT-3 responses
async def gpt_response(user_message, test_id):
    # Use GPT-3 for the response, here we're using a mock response
    conversation_history = conversation_memory.get(test_id, [])
    conversation_history.append({"role": "user", "content": user_message})
    
    # A system prompt to simulate the behavior of a sales assistant bot
    system_prompt = "You are a helpful sales assistant providing information about products."
    
    messages = [{"role": "system", "content": system_prompt}] + conversation_history
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7,
        max_tokens=150
    )
    
    # Save the updated conversation history
    bot_response = response['choices'][0]['message']['content']
    conversation_memory[test_id] = messages + [{"role": "assistant", "content": bot_response}]
    return bot_response

# Initialize the bot application
def main():
    # Initialize _bot_application variable here
    _bot_application = None

    if _bot_application is not None:
        print("Stopping previously running bot application...")
        if _bot_application.running:
            asyncio.run(_bot_application.stop())
        _bot_application = None
        print("Previous bot application stopped.")

    _bot_application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    _bot_application.add_handler(CommandHandler('start', start_command))
    _bot_application.add_handler(CommandHandler('other', other_command))
    _bot_application.add_handler(CommandHandler('help', help_command))
    
    _bot_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot polling started...")
    _bot_application.run_polling(drop_pending_updates=True, poll_interval=1)

if __name__ == '__main__':
    main()
