import os
import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv

# Load environment variables (API keys)
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_1_TOKEN")
OPENAI_API_KEY = os.getenv("aluraagency_OPEPNAI_API_KEY")
openai.api_key = OPENAI_API_KEY

conversation_memory = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    test_id = update.message.text.split(' ')[1]  # Extract Test ID from the /start command
    if test_id not in conversation_memory:
        await update.message.reply_text(f"Test ID {test_id} not found. Please try again.")
        return
    await update.message.reply_text(f"TestID {test_id} is confirmed. Start chatting!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text  # Get the message from the user
    if user_message.startswith('/start'):
        test_id = user_message.split(" ")[1]  # Extract Test ID from the /start command
        if test_id not in conversation_memory:
            await update.message.reply_text(f"Test ID {test_id} not found. Please try again.")
            return
        await update.message.reply_text(f"TestID {test_id} is confirmed. Start chatting!")

    else:
        # Respond using GPT-3 model for a sales assistant or customer bot
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
