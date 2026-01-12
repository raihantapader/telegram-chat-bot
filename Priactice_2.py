# customer_bot_1.py

import os
import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from datetime import datetime
from dotenv import load_dotenv
from db import insert_message  


load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_1_TOKEN")
openai.api_key = os.getenv("aluraagency_OPEPNAI_API_KEY")

CONVERSATION_ID = "563964"
VA_bot = "@raihantapader"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi, I'm interested in purchasing a new product. Can you help me choose the right one?")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    chat_id = update.message.chat.id  # Use the chat ID to track the conversation
    
    if update.message.from_user.username == VA_bot.lstrip('@'):  # Check if it's a customer message
        bot_role = "customer"
    else:
        bot_role = "salesperson"
    
    # Insert customer message into the database
   # insert_message( conversation_id=CONVERSATION_ID, customer_bot=customer_bot, role="salesperson", text=user_message, chat_id=chat_id)
    insert_message(conversation_id=CONVERSATION_ID, bot=VA_bot, role=bot_role, text=user_message, chat_id=chat_id)
     
    # Get the response from Salesperson's reply
    response = await gpt_response(user_message)

    # Insert salesperson message into the database
    #insert_message( conversation_id=CONVERSATION_ID, customer_bot=customer_bot, role="customer", text=response, chat_id=chat_id)
    insert_message(conversation_id=CONVERSATION_ID, bot="customerBot_1", role="customer", text=response, chat_id=chat_id)
    # Send the response back to the user (customer)
    await update.message.reply_text(response)


# GPT-3 response generation for the salesperson conversation
async def gpt_response(user_message):
    system_prompt = """
    You are an expert general customer assistant interacting with a salesperson.
    
    1. Your role is to behave like a real customer who interacts with a sales executive.
    2. You ask natural, realistic, and varied questions related to products and services.
    3. Your ask randomly any product and service with salesperson.
    4. Always must be try to remember you are a real customer who need to know about product or services, disocunt, availability, specifications etc naturally in english.
     
    """
    conversation_history = [{"role": "system", "content": system_prompt}]
    conversation_history.append({"role": "user", "content": user_message})

    response = openai.ChatCompletion.create(
        model="ft:gpt-3.5-turbo-0125:personal:your-fine-tuned-model-name:Cr1QtYEb",  # You can use your fine-tuned model here
        messages=conversation_history,
        temperature=0.5,
        max_tokens=100
    )

    return response['choices'][0]['message']['content']


# Initialize the bot
def main():
    _bot_application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers for different commands
    _bot_application.add_handler(CommandHandler('start', start))
    _bot_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Customer_1 Bot is running....")
    _bot_application.run_polling(drop_pending_updates=True, poll_interval=1)

if __name__ == '__main__':
    main()
