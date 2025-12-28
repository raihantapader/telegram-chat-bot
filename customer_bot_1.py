import os
import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv

# Load environment variables (API keys)
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_5_TOKEN")
aluraagency_OPEPNAI_API_KEY = os.getenv("aluraagency_OPEPNAI_API_KEY")
openai.api_key = aluraagency_OPEPNAI_API_KEY

conversation_memory = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Split the command text and check if there's a valid Test ID
    if len(update.message.text.split(' ')) > 1:
        test_id = update.message.text.split(' ')[1]  # Extract Test ID from the /start command
        if test_id not in conversation_memory:
            await update.message.reply_text(f"Test ID {test_id} not found. Please try again.")
            return
        await update.message.reply_text(f"TestID {test_id} is confirmed. Start chatting!")
        await update.message.reply_text(f"Your Test ID: {test_id}")  # Show the Test ID to the user for confirmation
        
        # Print the Test ID for logging purposes to verify
        print(f"Test ID assigned: {test_id}")
    else:
        await update.message.reply_text("Please provide a valid Test ID after the /start command.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    test_id = update.message.chat.id  # Use Telegram chat ID as the Test ID temporarily

    if test_id not in conversation_memory:
        await update.message.reply_text("Please type /start to initiate the conversation with a unique ID.")
        return

    # Log the Test ID being used
    print(f"Test ID being used for this message: {test_id}")

    bot_response = await gpt_response(user_message, test_id)
    await update.message.reply_text(f"TestID: {test_id}\n{bot_response}")

async def gpt_response(user_message, test_id):
    system_prompt = """
You are an expert helpful general customer assistant who talks with a sales assistant.
Your role is to behave like a real customer who interacts with a sales executive to know information about product and services.
You ask natural, realistic, and varied questions related to products and services, and you respond as a customer would in a real-world sales scenario.
"""
    
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}]
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7,
        max_tokens=150
    )

    bot_response = response['choices'][0]['message']['content']
    return bot_response

def main():
    _bot_application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    _bot_application.add_handler(CommandHandler('start', start))
    _bot_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Customer Bot polling started...")
    _bot_application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
