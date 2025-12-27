from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

async def start_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    test_id = context.args[0]  # Get the Test ID from the command
    await update.message.reply_text(f"Test ID {test_id} accepted! Let's start the conversation.")

    # You can also simulate customer queries here, e.g.
    await update.message.reply_text("What is the price of the product?")

# Setup the Test Bot (Customer Bot)
def main():
    # Test Bot token (replace with actual bot token)
    test_bot_token = "TELEGRAM_BOT_1_TOKEN"

    # Build the bot application
    application = ApplicationBuilder().token(test_bot_token).build()

    # Add handlers for commands
    application.add_handler(CommandHandler("start", start_test))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
