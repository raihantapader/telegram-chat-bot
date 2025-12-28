import os
import asyncio
import nest_asyncio  # Import nest_asyncio to allow nested event loops
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import openai

# Apply nest_asyncio to allow nested event loops, which is required for environments like Jupyter
nest_asyncio.apply()

# Load environment variables from the .env file
load_dotenv()

# Access API keys using os.getenv()
STARTER_BOT_TOKEN = os.getenv("TELEGRAM_BOT_5_TOKEN")
OPENAI_API_KEY = os.getenv("aluraagency_OPEPNAI_API_KEY")

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY

# Define the GPT response function
async def gpt_response(user_message):
    response = openai.ChatCompletion.create(
        model="ft:gpt-3.5-turbo-0125:personal:your-fine-tuned-model-name:CrGNWrcX",  # Make sure this is the correct model ID
        messages=[
            {"role": "system", "content":""" You are an expert helpful general customer assistant who talks with a sales assistant.
Your role is to behave like a real customer who interacts with a sales executive to know information about product and services.
You ask natural, realistic, and varied questions related to products and services, and you respond as a customer would in a real-world sales scenario. """},
            {"role": "user", "content": user_message}
        ],
        temperature=0.7,
        max_tokens=150
    )
    return response['choices'][0]['message']['content']

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! Welcome to the Bot. Please write /help to see the commands available.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(""" Available Commands:
   
    /linkedin - To get the LinkedIn profile URL
    /facebook - To get Facebook profile URL """)

# Command responses
async def linkedin_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("LinkedIn URL => https://www.linkedin.com/in/raihan-tapader06/")


async def facebook_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Facebook URL => https://www.facebook.com/raihantapader06/")


# Handle user messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text  # Get the message from the user
    bot_response = await gpt_response(user_message)
    await update.message.reply_text(bot_response)

# Handle unknown commands
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Sorry '{update.message.text}' is not a valid command")

async def unknown_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Sorry I can't recognize you, you said '{update.message.text}'")

# Main function to initialize the bot
def main():
    # Build the bot application
    application = ApplicationBuilder().token(STARTER_BOT_TOKEN).build()

    # Command Handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('linkedin', linkedin_url))
    application.add_handler(CommandHandler('facebook', facebook_url))

    # Message Handlers for unknown commands and text
    application.add_handler(MessageHandler(filters.COMMAND, unknown))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the bot
    print("Bot polling started...")
    application.run_polling(drop_pending_updates=True, poll_interval=1)

if __name__ == '__main__':
    main()
