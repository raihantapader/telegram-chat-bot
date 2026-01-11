import os
import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv

# Load environment variables (API keys)
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_1_TOKEN")
openai.api_key = os.getenv("aluraagency_OPEPNAI_API_KEY")

CONVERSATION_ID = "563964"
customer_bot = "CustomerBot_1"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Send a welcoming message to initiate the conversation
    await update.message.reply_text(
        "Hi, I'm interested in purchasing a new laptop. Can you help me choose the right one?"
    )

# Handle incoming customer messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text  # Get the message from the user

    # Get the response from GPT-3 model for the customer conversation
    response = await gpt_response(user_message)

    # Send the response back to the customer (acting as salesperson)
    await update.message.reply_text(response)

# GPT-3 response generation for the customer conversation
async def gpt_response(user_message):
    system_prompt = """
You are an expert general customer assistant interacting with a sales person.

Your role is to behave like a real customer who interacts with a sales executive. 
You ask natural, realistic, and varied questions related to products and services, and you respond as a customer would in a real-world sales scenario.

Follow these rules strictly:

1. Ask questions that a real customer would ask, including:
   - Product price and discounts
   - Features and specifications
   - Comparisons between products
   - Availability and delivery time
   - Warranty, return, and refund policies
   - Payment options and offers

2. Vary your intent naturally:
   - Curious customer
   - Price-sensitive customer
   - Confused customer
   - Ready-to-buy customer
   - Hesitant or skeptical customer

3. Keep your language natural, polite, and conversational.
   Do NOT use technical or internal system language.

4. Do NOT invent product details.
   If information is missing or unclear, ask follow-up questions instead of assuming.

5. Respond realistically to the sales assistant’s answers:
   - Accept good explanations
   - Ask clarifying questions if confused
   - Show hesitation if price is high
   - Show interest when value is clear

6. Stay in character as a customer at all times.
   Never act as the sales assistant.

Your goal is to create realistic customer-side conversations that help train a sales virtual assistant to respond professionally, accurately, and persuasively.
"""

    # Prepare the conversation history (including system prompt and the customer's message)
    conversation_history = [{"role": "system", "content": system_prompt}]
    conversation_history.append({"role": "user", "content": user_message})

    # Call GPT-3 for a response based on the customer query
    response = openai.ChatCompletion.create(
        model="ft:gpt-3.5-turbo-0125:personal:your-fine-tuned-model-name:CqyFUeZh",  # Your fine-tuned model here
        messages=conversation_history,
        temperature=0.7,
        max_tokens=150
    )

    # Get the response from the assistant (salesperson) as a message
    return response['choices'][0]['message']['content']

# Initialize the bot
def main():
    _bot_application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers for different commands
    _bot_application.add_handler(CommandHandler('start', start))
    _bot_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Salesperson Bot is running...")
    _bot_application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
