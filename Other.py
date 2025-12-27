# Starter Bot old code

import os
import openai
import nest_asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from uuid import uuid4

nest_asyncio.apply()

load_dotenv()

STARTER_BOT_TOKEN = os.getenv("STARTER_BOT_TOKEN")
TELEGRAM_BOTS_TOKENS = [
    os.getenv("TELEGRAM_BOT_1_TOKEN"),
    os.getenv("TELEGRAM_BOT_2_TOKEN"),
    os.getenv("TELEGRAM_BOT_3_TOKEN"),
    os.getenv("TELEGRAM_BOT_4_TOKEN"),
    os.getenv("TELEGRAM_BOT_5_TOKEN"),
]

openai.api_key = os.getenv("OPENAI_API_KEY")

# A dictionary to store the unique ID for each customer bot
customer_bot_ids = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Generate a unique ID for each customer bot
    for bot_token in TELEGRAM_BOTS_TOKENS:
        customer_bot_ids[bot_token] = str(uuid4())

    # Send the unique IDs to the Starter Bot's chat
    await update.message.reply_text(f"Hey! I'm the Starter Bot. I start the chat. Use /newtest to create a new reply Unique IDs: {customer_bot_ids}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get the incoming message from the Starter Bot
    user_message = update.message.text

    # Identify which bot is sending the message (by checking token or user ID)
    bot_token = update.message.chat.id
    customer_id = customer_bot_ids.get(str(bot_token), None)

    if customer_id:
        # Send the message to the Sales Bot (your AI assistant)
        response = await gpt_response(user_message, customer_id)
        await update.message.reply_text(response)
    else:
        await update.message.reply_text("No valid bot ID found.")

async def gpt_response(user_message, customer_id):
    # Send the message to OpenAI for generating a response from the Sales Bot (acting as the salesperson)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"You are a sales person talking to a customer. Customer ID: {customer_id}."},
            {"role": "user", "content": user_message}
        ],
        temperature=0.7,
        max_tokens=150
    )
    return response['choices'][0]['message']['content']

def main():
    # Initialize the Starter Bot
    application = ApplicationBuilder().token(STARTER_BOT_TOKEN).build()

    # Handlers for the bot commands and messages
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot
    print("Starter bot running...")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()




# Customer1 bot old code:
import os
import asyncio
import nest_asyncio  # Import nest_asyncio to allow nested event loops
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import openai

nest_asyncio.apply()

load_dotenv()

TELEGRAM_BOT_1_TOKEN = os.getenv("TELEGRAM_BOT_1_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY

async def gpt_response(user_message):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # 
        messages=[
            {"role": "system", "content":
                """
You are an expert customer assistant interacting with a sales executive or sales virtual assistant.

Follow these specific guidelines strictly:

1. **Ask Product-Related Questions:**
   - Inquire about **product features**, such as:
     - "What are the specifications of this product?"
     - "Does it have any special features?"
   - Ask about **price** and **discounts**:
     - "How much does this product cost?"
     - "Are there any discounts or special offers available?"
   - Inquire about **warranty**, **return policy**, and **support**:
     - "What is the warranty period?"
     - "Can I return the product if it doesn't meet my expectations?"
     - "Is customer support available for this product?"
   
2. **Request Availability Information:**
   - Ask about **stock availability** and **delivery time**:
     - "Is this product available in stock?"
     - "When can I expect it to be delivered?"
   
3. **Consider Payment and Financing Options:**
   - Ask about **payment options** and **installment plans**:
     - "What are the payment methods accepted?"
     - "Can I pay in installments?"
   - Ask about **EMI (Equated Monthly Installments)** options if available:
     - "Can I avail an EMI option for this product?"
   
4. **Price Sensitivity:**
   - Display **hesitation about price** if the product is expensive:
     - "This is quite expensive, can you offer any discounts?"
     - "Can I get a better price if I buy multiple items?"
   - Ask about **cheaper alternatives** if the product seems too costly:
     - "Do you have a more affordable version of this product?"

5. **Curiosity or Readiness to Buy:**
   - Show **curiosity** about the product or its alternatives:
     - "What’s the difference between this product and the other model?"
     - "Are there any new features in the latest version?"
   - **Show interest in buying** if satisfied with the response:
     - "How do I proceed with purchasing this product?"
     - "Is there an option to schedule a demo?"
   
6. **Follow-Up Questions:**
   - **Ask for clarification** if any details are unclear:
     - "Can you explain more about the return policy?"
     - "How does the warranty work? Does it cover accidental damage?"
   - **Request additional details** if the answer is not fully satisfactory:
     - "Can you provide more information on how the payment process works?"

7. **Never Act as a Sales Assistant:**
   - **Do not give product descriptions** or information that should come from the sales assistant. Always ask questions and show interest as a customer.
   - **Do not assume answers**; always ask for confirmation or additional details when unsure about something.

### Example Customer Interactions:

- **Example 1:**
  - **User**: "How much does this laptop cost?"
  - **Assistant**: "The laptop costs $1200 and comes with a 1-year warranty."
  - **User**: "Is there a discount for this laptop?"
  - **Assistant**: "Yes, we have a 10% discount if you pay in full."
  
- **Example 2:**
  - **User**: "What’s the warranty on this phone?"
  - **Assistant**: "The phone comes with a 1-year warranty."
  - **User**: "Can I return the phone if I don’t like it?"
  - **Assistant**: "Yes, we offer a 30-day return policy."
  
- **Example 3:**
  - **User**: "Can I pay for this item in installments?"
  - **Assistant**: "Yes, we offer an EMI plan for 6 months."
  - **User**: "How do I apply for the EMI option?"

8. **Add Realistic Follow-Up Behavior:**
   - If the price or terms are unclear or unsatisfactory, ask for clarification or alternatives:
     - "Can you provide any cheaper alternatives?"
     - "Is there an option to buy this with a discount if I buy more than one?"

---

### **Key Points for Fine-Tuning the Model:**
1. **Behavioral Consistency**: The model must consistently act as a customer who is either **curious**, **price-sensitive**, **hesitant**, or **ready to buy**. The tone should be polite and natural.
2. **Clear Role Understanding**: The model should never **give sales information** but only **ask questions**. This allows the sales assistant to respond and guide the customer.
3. **Adaptable Responses**: The model must adapt to the answers from the assistant, show interest when the assistant provides helpful details, and ask for clarification when needed.
4. **Engagement in Conversation**: The customer should show **interest in the product** and not jump straight to buying without asking questions. It’s essential to simulate **interest** and **engagement**.

---

### **Example of a Complete Prompt for GPT:**
```plaintext
You are a realistic customer interacting with a sales assistant.

Your goal is to ask questions and gather information about a product before deciding to purchase. Your questions should cover:
- Product features, pricing, availability, and delivery time
- Discounts, payment options, and warranty
- Comparison with other products and alternatives

Rules:
- Ask specific and relevant questions, and be natural in your responses.
- Never act as a sales assistant. Always stay in character as a customer.
- If you are satisfied with the answer, show interest in buying the product and ask about the next steps.
- If you are not satisfied, ask for further clarification or request better terms.

Example Scenario:
User: "How much does this phone cost?"
Assistant: "The phone costs $800."
User: "Is there any discount available for the phone?"
Assistant: "Yes, there’s a 10% discount available."
User: "Can I get the phone in installments?"
Assistant: "Yes, we offer EMI options."
User: "Great! How do I proceed with the purchase?"
     
             """ },
            {"role": "user", "content": user_message}
        ],
        temperature=0.7,
        max_tokens=150
    )
    return response['choices'][0]['message']['content']

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! Welcome to the Customer Bot.")

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
    application = ApplicationBuilder().token(TELEGRAM_BOT_1_TOKEN).build()

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
