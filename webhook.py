import os
import uuid
import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv
from db import insert_message, create_test, test_exists

# Load environment variables (API keys)
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("STARTER_BOT_TOKEN")  # Your starter bot token
openai.api_key = os.getenv("aluraagency_OPEPNAI_API_KEY")  # Your OpenAI API key

conversation_memory = {}  # Store conversation history based on Test ID

# Function to start the conversation and generate a unique Test ID
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Generate a unique Test ID (e.g., FJF2TD)
    test_id = str(uuid.uuid4().hex[:6]).upper()  # Generate a 6-character Test ID
    conversation_memory[test_id] = []  # Initialize conversation history for this Test ID
    
    # Save the Test ID to the database (store conversation with "customer" role)
    create_test(test_id, update.message.chat.id)

    # Send the generated Test ID to the user
    await update.message.reply_text(
        f"✅ *Reply Speed Test Created!* \n\n"
        f"Test ID: `{test_id}`\n\n"
        f"Start Conversation. . . 🚀\n\n"
        f"Happy testing . . . 🚀"
        , parse_mode="Markdown"
    )

# Handle incoming messages and generate responses using GPT-3 model
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    test_id = update.message.chat.id  # Use chat ID as the Test ID temporarily

    # Check if Test ID exists
    if not test_exists(test_id):
        await update.message.reply_text("Please use /start to initiate the conversation with a Test ID.")
        return

    # Get the response from GPT-3 model for customer conversation
    response = await gpt_response(user_message, test_id)

    # Store the response in the database (insert the message)
    insert_message(test_id, "starter_bot", "customer", user_message, update.message.chat.id)
    insert_message(test_id, "salesperson_bot", "salesperson", response, update.message.chat.id)

    # Send the response back to the user (customer)
    await update.message.reply_text(response)

# GPT-3 response generation for customer conversation
async def gpt_response(user_message, test_id):
    system_prompt = """
You are an expert general customer assistant interacting with a salesperson.

Your role is to behave like a real customer who interacts with a salesperson.
You ask natural, realistic, and varied questions related to products and services, and you respond as a customer would in a real-world sales scenario.
"""
    
    # Prepare the message to send to GPT-3
    conversation_history = [{"role": "system", "content": system_prompt}]
    conversation_history.append({"role": "user", "content": user_message})

    # Call GPT-3 for a response based on the customer query
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

    _bot_application.add_handler(CommandHandler('start', start))
    _bot_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    _bot_application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
