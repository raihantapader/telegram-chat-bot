import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from collections import deque

# Load OpenAI API Key
openai.api_key = "OPENAI_API_KEY"

# Initialize a queue to handle customer queries sequentially
customer_queue = deque()

# Function to generate GPT response for the VA Bot
async def gpt_response(user_message):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert sales assistant. Your work is to reply customer queries with politeness and professionalism are key to customer satisfaction."},
            {"role": "user", "content": user_message}
        ],
        temperature=0.7,
        max_tokens=150
    )
    return response['choices'][0]['message']['content']

# Function to handle incoming customer queries
async def handle_customer_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    test_id = context.args[0]  # Test ID for logging
    user_message = update.message.text  # Get message from the customer bot
    
    # Add the customer's message to the queue
    customer_queue.append((test_id, user_message))
    
    # Process the next message in the queue
    if customer_queue:
        test_id, customer_message = customer_queue.popleft()
        bot_response = await gpt_response(customer_message)
        
        # Reply to the customer bot
        await update.message.reply_text(bot_response)

# Initialize the VA Bot (Sales Bot)
def main():
    sales_bot_token = "VA_BOT_TOKEN"
    application = ApplicationBuilder().token(sales_bot_token).build()

    # Add message handler for customer messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_customer_message))

    application.run_polling()

if __name__ == '__main__':
    main()
