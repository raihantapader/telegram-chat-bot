import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("aluraagency_OPEPNAI_API_KEY")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    test_id = update.message.text.split(" ")[1]
    await update.message.reply_text(f"TestID: {test_id} is confirmed. Start chatting!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    test_id = update.message.chat.id

    if test_id not in test_id_storage:
        await update.message.reply_text("Please use /start to generate a TestID.")
        return

    response = await gpt_response(user_message, test_id)
    await update.message.reply_text(response)

async def gpt_response(user_message, test_id):
    system_prompt = "You are an expert customer assistant interacting with a sales person."
    
    # Prepare the message to send to GPT-3 for customer conversation
    conversation_history = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation_history,
        temperature=0.7,
        max_tokens=150
    )
    
    return response['choices'][0]['message']['content']

def start_customer_bot():
    application = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_1_TOKEN")).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == "__main__":
    start_customer_bot()
