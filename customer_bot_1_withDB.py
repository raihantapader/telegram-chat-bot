import os
from urllib import response
import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime
from db import insert_message  # Import the database function

load_dotenv()


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_1_TOKEN")
openai.api_key = os.getenv("aluraagency_OPEPNAI_API_KEY")

# MongoDB Connection Setup
MONGODB_URI = os.getenv("MONGODB_URI")  
client = MongoClient(MONGODB_URI)
db = client['Telegram_chatbot']  # Database
chat_bot_collection = db['chat_bot']  # Collection for storing conversations

# Function to insert messages into the database
def insert_message(role: str, text: str, chat_id: int):
    message = {
        "role": role,  # 'customer' or 'salesperson'
        "text": text,
        "chat_id": chat_id,
        "timestamp": datetime.now()  
    }
    chat_bot_collection.insert_one(message)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(response)


# Handle incoming messages (customer queries and salesperson replies)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    chat_id = update.message.chat.id  # Use the chat ID to track the conversation

    # Insert salesperson message into the database
    insert_message(role="salesperson", text=user_message, chat_id=chat_id)

    # Get the response from GPT-3 (Salesperson's reply)
    response = await gpt_response(user_message)

    # Insert customer message into the database
    insert_message(role="customer", text=response, chat_id=chat_id)

    # Send the response back to the user (customer)
    await update.message.reply_text(response)


async def gpt_response(user_message):
    system_prompt = """
    You are an expert general customer assistant interacting with a salesperson.
    
    Your role is to behave like a real customer who interacts with a sales executive.
    You ask natural, realistic, and varied questions related to products and services.
    """
    conversation_history = [{"role": "system", "content": system_prompt}]
    conversation_history.append({"role": "user", "content": user_message})

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", 
        messages=conversation_history,
        temperature=0.7,
        max_tokens=150
    )

    return response['choices'][0]['message']['content']


# Initialize the bot
def main():
    _bot_application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers for different commands
    _bot_application.add_handler(CommandHandler('start', start))
    _bot_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    _bot_application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
