# https://medium.com/@mikez_dg/creating-a-simple-but-interactive-telegram-bot-with-python-a-complete-guide-d713f8b6c3d7

#Prerequisites
#Before we begin, ensure you have the following:
   # 1. Python 3.6+ installed on your computer.
   # 2. A Telegram account.
   # 3. The python-telegram-bot library installed. You can install it using pip:
         # pip install python-telegram-bot --upgrade


# Step 1: Get a Telegram Bot Token
     # - BotFather will give you a token after you create a new bot. 
     
     
# Step 2: Setting Up Your Python Script
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, Application, ContextTypes

# Replace 'YOUR_API_TOKEN' with your actual bot token from BotFather
API_TOKEN = 'TELEGRAM_BOT_1_TOKEN'



# Step 3: Writing Asynchronous Bot Handlers
    # - You’ll define several async functions to handle different commands and interactions.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Welcome to the Simple Telegram Bot!")  # Start Command
    await show_option_buttons(update, context)


# Displaying Option Buttons
    # - This function sends a message with inline buttons for user interaction.
async def show_option_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Option 1", callback_data='button_1')],
        [InlineKeyboardButton("Option 2", callback_data='button_2')],
        [InlineKeyboardButton("Option 3", callback_data='button_3')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please choose an option:', reply_markup=reply_markup)

# Handling Button Selections
     # - This function processes the button clicks and responds accordingly.
async def button_selection_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(f'You selected option: {query.data.split("_")[1]}')


# Step 4: Adding More Commands
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        'I can respond to the following commands:\n/start - Start the bot\n/help - Get help information'
    )


# Step 5: Running the Bot
def main():
    # Create the Application instance
    application = Application.builder().token(API_TOKEN).build()

    # Register command and message handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))

    # Register a CallbackQueryHandler to handle button selections
    application.add_handler(CallbackQueryHandler(button_selection_handler, pattern='^button_'))

    # Start the bot
    application.run_polling()


if __name__ == '__main__':
    main()