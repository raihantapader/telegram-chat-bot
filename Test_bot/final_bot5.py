import os
from openai import OpenAI
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
import random
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_5_TOKEN")  # Change for each bot
OPENAI_API_KEY = os.getenv("aluraagency_OPEPNAI_API_KEY")
BOT_NAME = os.getenv("CUSTOMER_5_BOT_USERNAME", "customerBot_5")  # Change for each bot

client = OpenAI(api_key=OPENAI_API_KEY)

# MongoDB connection
MongoDB_Url = os.getenv("MONGODB_URI")
mongo_client = MongoClient(MongoDB_Url)
db = mongo_client['Raihan']
test_collection = db['active_test_ids']
chat_collection = db['chat_bot']

VA_bot = "@raihantapader"

conversation_histories = {}

PRODUCT_POOL = [
    "a new laptop for work", "wireless headphones", "a smartwatch", "a gaming console",
    "a tablet", "a camera", "a fitness tracker", "a Bluetooth speaker", "a drone",
    "noise-cancelling earbuds", "a monitor", "an e-reader", "a power bank",
]

SYSTEM_PROMPT = """
YOU ARE A CUSTOMER. YOU ARE NOT A SALESPERSON.

## YOUR ROLE:
🛒 YOU ARE THE CUSTOMER
💰 YOU ARE BUYING
❓ YOU ASK QUESTIONS
🤔 YOU MAKE DECISIONS
🙋 YOU ARE BEING SERVED

NEVER ACT AS A SALESPERSON!
"""


def get_latest_test_id():
    """Get the most recent active test_id from database"""
    try:
        latest_test = test_collection.find_one(
            {"status": "active"},
            sort=[("created_at", -1)]
        )
        
        if latest_test:
            test_id = latest_test['test_id']
            print(f"✅ Retrieved latest Test ID from database: {test_id}")
            return test_id
        else:
            print("⚠️  No active test_id found in database. Using default.")
            return "default"
    except Exception as e:
        print(f"❌ Error retrieving test_id: {e}")
        return "default"


def insert_message(conversation_id: str, role: str, text: str, chat_id: int, bot_name: str):
    """Insert message into database"""
    message = {
        "conversation_id": conversation_id,
        "bot": bot_name,
        "role": role,
        "text": text,
        "chat_id": chat_id,
        "timestamp": datetime.utcnow()
    }
    
    result = chat_collection.insert_one(message)
    print(f"[DB] Saved {role} message (ID: {result.inserted_id})")
    return result.inserted_id


def get_or_create_conversation_history(chat_id, test_id):
    """Get or create conversation history for a specific chat"""
    if chat_id not in conversation_histories:
        selected_product = random.choice(PRODUCT_POOL)
        
        conversation_system_prompt = SYSTEM_PROMPT + f"\n\nYou are interested in buying: {selected_product}"
        
        conversation_histories[chat_id] = {
            'messages': [{"role": "system", "content": conversation_system_prompt}],
            'product': selected_product,
            'created_at': datetime.now().isoformat(),
            'test_id': test_id
        }
        
        print(f"[INFO] New conversation: chat_id={chat_id}, test_id={test_id}, product={selected_product}")
    
    return conversation_histories[chat_id]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - gets latest test_id from database"""
    chat_id = update.message.chat.id
    
    # Get latest test_id from database
    test_id = get_latest_test_id()
    
    print(f"\n{'='*70}")
    print(f"🤖 {BOT_NAME} STARTED")
    print(f"{'='*70}")
    print(f"Test ID: {test_id}")
    print(f"Chat ID: {chat_id}")
    print(f"{'='*70}\n")

    # Get or create conversation history
    conv_history = get_or_create_conversation_history(chat_id, test_id)
    product = conv_history['product']
    
    # Generate initial customer greeting
    try:
        initial_prompt = f"You are a customer interested in buying {product}. Generate a brief, natural greeting (1-2 sentences)."
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a customer. Generate natural greetings."},
                {"role": "user", "content": initial_prompt}
            ],
            temperature=0.9,
            max_tokens=80
        )
        
        initial_message = response.choices[0].message.content.strip()
        print(f"[LLM] Generated: {initial_message}")
        
    except Exception as e:
        print(f"[ERROR] LLM failed: {e}")
        initial_message = f"Hi! I'm interested in buying {product}. Can you help?"
    
    # Send message to user
    await update.message.reply_text(
        f"✅ Started with Test ID: `{test_id}`\n\n{initial_message}",
        parse_mode="Markdown"
    )
    
    # Add to conversation history
    conv_history['messages'].append({
        "role": "assistant",
        "content": initial_message
    })
    
    # Save to database
    insert_message(
        conversation_id=test_id,
        role="customer",
        text=initial_message,
        chat_id=chat_id,
        bot_name=BOT_NAME
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages"""
    user_message = update.message.text
    chat_id = update.message.chat.id
    username = update.message.from_user.username if update.message.from_user.username else "unknown"
    
    # Get the most recent test_id
    test_id = get_latest_test_id()
    
    # Retrieve or create conversation history based on chat_id and test_id
    conv_history = get_or_create_conversation_history(chat_id, test_id)
    
    # Determine role
    if username == VA_bot.lstrip('@'):
        bot_role = "salesperson"
        print(f"[SALESPERSON] {user_message}")
    else:
        bot_role = "customer"
        print(f"[CUSTOMER] {user_message}")
    
    # Save incoming message
    insert_message(
        conversation_id=test_id,    # Use the correct test_id
        role=bot_role,
        text=user_message,
        chat_id=chat_id,
        bot_name=BOT_NAME if bot_role == "customer" else username
    )
    
    # Generate response if from salesperson
    if bot_role == "salesperson":
        response = await gpt_customer_response(user_message, chat_id)
        
        print(f"[CUSTOMER-AI] {response}")
        
        # Save customer response
        insert_message(
            conversation_id=test_id,
            role="customer",
            text=response,
            chat_id=chat_id,
            bot_name=BOT_NAME
        )
        
        await update.message.reply_text(response)


async def gpt_customer_response(salesperson_message, chat_id):
    """Generate customer response using GPT"""
    conv_history = get_or_create_conversation_history(chat_id, get_latest_test_id())
    
    conv_history['messages'].append({
        "role": "user",
        "content": salesperson_message
    })
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=conv_history['messages'],
            temperature=0.85,
            max_tokens=150,
            top_p=0.92,
            frequency_penalty=0.5,
            presence_penalty=0.5,
        )
        
        customer_response = response.choices[0].message.content.strip()
        
        # Add to history
        conv_history['messages'].append({
            "role": "assistant",
            "content": customer_response
        })
        
        return customer_response
        
    except Exception as e:
        print(f"[ERROR] {e}")
        return "Sorry, I'm having trouble responding."


def main():
    if not TELEGRAM_BOT_TOKEN:
        print("[ERROR] TELEGRAM_BOT_TOKEN not found!")
        return

    if not OPENAI_API_KEY:
        print("[ERROR] OPENAI_API_KEY not found!")
        return
    
    _bot_application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    _bot_application.add_handler(CommandHandler('start', start))
    _bot_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("="*70)
    print(f"{BOT_NAME} IS RUNNING".center(70))
    print("="*70)
    print(f"\nBot will use the latest Test ID from database")
    print(f"Waiting for /start command...\n")
    
    _bot_application.run_polling(drop_pending_updates=True, poll_interval=1)

if __name__ == '__main__':
    main()