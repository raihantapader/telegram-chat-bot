import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

async def handle_sales_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    # Here, simulate the salesperson's response. (Replace this with an actual sales bot logic)
    sales_response = f"Sales Bot Reply: {user_message} - Thank you for reaching out! How can I assist you further?"
    await update.message.reply_text(sales_response)

def start_sales_bot():
    application = ApplicationBuilder().token(os.getenv("VA_BOT_TOKEN")).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sales_message))
    application.run_polling()

if __name__ == "__main__":
    start_sales_bot()
