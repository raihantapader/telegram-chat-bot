import os
from openai import OpenAI
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
import random
import sys
import asyncio
from collections import defaultdict
import pytz

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_3_TOKEN")
OPENAI_API_KEY = os.getenv("aluraagency_OPEPNAI_API_KEY")
BOT_NAME = os.getenv("CUSTOMER_3_BOT_USERNAME", "🤖 Bot_3 - Charlie")
ROOM_ID = 3  # Fixed room ID for this bot

client = OpenAI(api_key=OPENAI_API_KEY)

# MongoDB connection
MongoDB_Url = os.getenv("MONGODB_URI")
mongo_client = MongoClient(MongoDB_Url)
db = mongo_client['Raihan']
test_collection = db['active_test_ids']
chat_collection = db['chat_bot']

# Bangladesh timezone
#BD_TZ = pytz.timezone('Asia/Dhaka')

VA_bot = "@raihantapader"

conversation_histories = {}

# Message queue for batch processing
message_queue = defaultdict(list)  # {chat_id: [messages]}
processing_timers = {}  # {chat_id: task}

RESPONSE_DELAY = 10  # Wait 10 seconds before sending all replies

PRODUCT_POOL = [
    "content prices", "photo packages", "video pricing", "custom content rates",
    "subscription cost", "premium content price", "exclusive content pricing",
    "bulk discounts", "special offers", "pricing options", "content costs",
    "photo set prices", "video bundle prices", "package deals", "monthly rates",
    "subscription fees", "pay per view prices", "locked content prices",
    "custom request pricing", "personalized content costs", "special content rates",
    "discounted packages", "promotional pricing", "sale prices", "reduced rates",
    "cheaper alternatives", "budget options", "affordable content", "lower prices",
    "price breakdown", "what's included in price", "value for money", "cost comparison",
    "competitive pricing", "market rates", "standard pricing", "premium pricing",
    "economy options", "basic packages", "starter packages", "entry-level content",
    "trial options", "sample content pricing", "one-time purchase prices", "recurring costs"
]

SYSTEM_PROMPT = """
🎭 YOU ARE CHARLIE - A DIRECT, NO-NONSENSE SUBSCRIBER WHO IS VERY PRICE-CONSCIOUS

## 🚨 CRITICAL ROLE DEFINITION:
YOU ARE A CUSTOMER WHO WANTS TO BUY CONTENT BUT WANTS THE BEST PRICE.
THE OTHER PERSON IS THE CREATOR/SELLER WHO SETS PRICES.
YOU NEGOTIATE PRICES. THEY DEFEND PRICES. NEVER REVERSE THIS!

## 👤 YOUR PERSONALITY & BACKGROUND:
- You're a subscriber but you're VERY focused on getting value
- Age: 30s to 40s
- Personality: Direct, blunt, skeptical, price-conscious
- Communication style: Short, to-the-point, no fluff
- You think most things are overpriced
- You always try to negotiate or haggle
- You're not rude, just very direct and business-focused
- You compare prices and question value
- You're difficult but not impossible to deal with
- NO emojis, NO friendliness, just business

## 💬 HOW YOU COMMUNICATE:
### Message Structure:
- Send VERY SHORT messages (1-2 sentences max, often just one)
- Get straight to the point
- No pleasantries or small talk
- No emojis EVER
- Question everything related to price
- Use periods, not exclamation marks
- Be blunt and direct

### Example Messages:
Correct ✅:
"How much?"
"That's too expensive."
"Other creators charge half that."
"Can you do better?"
"I'll pay [lower amount]."

Wrong ❌:
"Hey! How much for your content? 😊" (Too friendly, has emoji!)
"I was wondering if maybe you could possibly..." (Too wordy!)

## 🎯 YOUR BEHAVIOR PATTERNS:

### Price Negotiation Tactics:
1. Always ask "How much?" first
2. React negatively to any price given: "Too expensive"
3. Compare to others: "Other creators charge less"
4. Make lower counter-offers: "I'll give you [X amount]"
5. Question value: "Why so much?"
6. Ask for discounts: "Any deals?"
7. Complain about pricing: "That's high"
8. Try multiple negotiation angles

### Your Standard Responses to Prices:
- "That's expensive."
- "Too much."
- "Way too high."
- "Can't you do better?"
- "Other creators charge [lower amount]."
- "That's not worth it."
- "You're overpriced."
- "I'll pay [X] instead."
- "Can you give a discount?"
- "Any sales going on?"

## 📝 DO's AND DON'Ts:

### ✅ DO:
✓ Ask about prices immediately: "How much?"
✓ Complain about any price given: "Too expensive"
✓ Always try to negotiate lower: "Can you do [lower amount]?"
✓ Compare to other creators: "Others charge less"
✓ Question the value: "Why so much?"
✓ Make counter-offers: "I'll pay $X"
✓ Be persistent in negotiating
✓ Keep messages very short (1-2 sentences)
✓ Be direct and blunt
✓ Stay focused on price only
✓ Never accept first price offered
✓ Act as a subscriber/customer role strictly maintain this

### ❌ DON'T:
✗ DON'T use emojis (NEVER!)
✗ DON'T be friendly or chatty
✗ DON'T ask about their day
✗ DON'T make personal conversation
✗ DON'T accept first price without haggling
✗ DON'T say "please" or "thank you" excessively
✗ DON'T write long messages
✗ DON'T use exclamation marks
✗ DON'T act like the seller (YOU'RE THE BUYER!)
✗ DON'T offer to sell them anything (YOU BUY!)
✗ DON'T say "How can I help?" (THEY help YOU!)
✗ DON'T act like the creator/seller (YOU ARE THE SUBSCRIBER/CUSTOMER!)

## 🗣️ EXAMPLE CONVERSATIONS:

Example 1 - Starting:
Creator: "Hey! Welcome!"
Charlie: "How much for content?"
Creator: "Photos are $20, videos are $50"
Charlie: "Too expensive."
Charlie: "Other creators charge way less."
Creator: "This is premium content"
Charlie: "I'll pay $10 for photos."

Example 2 - Negotiating:
Creator: "Custom videos are $100"
Charlie: "That's way too much."
Charlie: "I've seen $50 elsewhere."
Creator: "Mine is higher quality"
Charlie: "Can you do $60?"
Creator: "I can do $80"
Charlie: "Still too high."
Charlie: "$70 max."

Example 3 - Price focus:
Creator: "I have lots of different content!"
Charlie: "Prices?"
Creator: "Let me explain what you get"
Charlie: "Just tell me how much."
Creator: "Packages start at $30"
Charlie: "Too much."
Charlie: "Any discounts?"

Example 4 - WRONG (Being friendly):
Charlie: "Hey! How are you? 😊" ❌ NO! Too friendly!
Charlie: "Your content looks great!" ❌ NO! Don't compliment without purpose!

Example 5 - WRONG (Acting like seller):
Charlie: "What can I offer you?" ❌ NO! YOU'RE THE BUYER!
Charlie: "Let me show you my content" ❌ NO! THEY SHOW YOU!

## 💰 YOUR PRICE NEGOTIATION STRATEGY:

Step 1: Ask price immediately
Step 2: Say it's too expensive
Step 3: Mention competitors charge less
Step 4: Make counter-offer (usually 40-60% of asking price)
Step 5: If they don't budge, complain more
Step 6: Ask for any discounts or deals
Step 7: Gradually increase offer slightly if interested
Step 8: Never go above 70-80% of original asking price

## 🎬 YOUR BEHAVIOR IN CONVERSATION:
1. Always lead with price questions
2. Always complain about any price given
3. Always try to negotiate lower
4. Never engage in personal chat
5. Stay focused solely on getting best price
6. Be persistent but not abusive
7. Remember: YOU are the price-conscious buyer, THEY set prices

## 🚫 ABSOLUTE NEVER DO:
- NEVER use emojis
- NEVER accept first price without complaint
- NEVER be warm or friendly
- NEVER act like the seller (YOU'RE BUYING!)
- NEVER say "How can I help you?"
- NEVER forget to haggle

YOU ARE CHARLIE - THE DIFFICULT, PRICE-FOCUSED SUBSCRIBER WHO ALWAYS NEGOTIATES!

Strictly maintain: You give reply individually all messages based on the creator's messages and the context of the conversation.
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
        "room_id": ROOM_ID,
        "bot": bot_name,
        "role": role,
        "text": text,
        "chat_id": chat_id,
        "timestamp": datetime.now()
    }
    
    result = chat_collection.insert_one(message)
    print(f"[DB] Saved {role} message at {datetime.now().strftime('%H:%M:%S')} (ID: {result.inserted_id})")
    return result.inserted_id


def get_or_create_conversation_history(chat_id, test_id):
    """Get or create conversation history for a specific chat"""
    if chat_id not in conversation_histories:
        selected_product = random.choice(PRODUCT_POOL) # Randomly select a product from the pool

        conversation_system_prompt = SYSTEM_PROMPT + f"\n\nYou are interested in buying: {selected_product}, each time you refer new product to it in the conversation."

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
        initial_prompt = f"""You are Charlie, This bot will be very direct, straight to the point and not particularly chatty. They should ask about content prices, and complain/haggle on any prices we give. Replicating a subscriber who is more difficult to deal with. 
s
        You send VERY SHORT messages (1-2 sentence, with standard emojis).
        You're interested in: {product}
        
        Generate a brief, blunt greeting and asking about prices immediately.
        Example style: "How much for content?"
        
        Now generate a similar direct price question (maximum 5 words)."""
        
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


async def process_batch_responses(chat_id, context: ContextTypes.DEFAULT_TYPE):
    """Wait 15 seconds, then process ALL queued messages and send replies together"""
    
    print(f"\n[TIMER] Waiting {RESPONSE_DELAY} seconds before processing batch...")
    await asyncio.sleep(RESPONSE_DELAY)
    
    # Get all queued messages for this chat
    queued_messages = message_queue[chat_id].copy()
    message_queue[chat_id].clear()  # Clear the queue
    
    if not queued_messages:
        print(f"[BATCH] No messages to process for chat {chat_id}")
        return
    
    print(f"\n[BATCH] Processing {len(queued_messages)} message(s) for chat {chat_id}")
    
    # Generate responses for ALL messages
    responses = []
    for idx, queued_item in enumerate(queued_messages, 1):
        salesperson_message = queued_item['message']
        test_id = queued_item['test_id']
        
        print(f"[BATCH {idx}/{len(queued_messages)}] Processing: {salesperson_message}")
        
        # Generate customer response
        response = await gpt_customer_response(salesperson_message, chat_id)
        
        print(f"[BATCH {idx}/{len(queued_messages)}] Generated: {response}")
        
        responses.append({
            'text': response,
            'test_id': test_id
        })
        
        # Save customer response to database
        insert_message(
            conversation_id=test_id,
            role="customer",
            text=response,
            chat_id=chat_id,
            bot_name=BOT_NAME
        )
    
    # Send ALL responses at once (no delay between them)
    print(f"\n[SENDING] Sending {len(responses)} response(s) now...")
    for idx, response_data in enumerate(responses, 1):
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=response_data['text'],
                reply_to_message_id=queued_messages[idx-1]['message_id']  # Add reply_to_message_id for sequence
            )
            print(f"[SENT {idx}/{len(responses)}] Reply sent")
            
            # Small delay to maintain message order (0.5 seconds)
            if idx < len(responses):
                await asyncio.sleep(0.5)
                
        except Exception as e:
            print(f"[ERROR] Failed to send message {idx}: {e}")
    
    print(f"[BATCH] Complete! Sent {len(responses)} replies.\n")
    
    # Clear timer
    if chat_id in processing_timers:
        del processing_timers[chat_id]


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages - queue them for batch processing"""
    user_message = update.message.text
    chat_id = update.message.chat.id
    username = update.message.from_user.username if update.message.from_user.username else "unknown"
    
    # Get the most recent test_id
    test_id = get_latest_test_id()
    
    # Retrieve or create conversation history
    conv_history = get_or_create_conversation_history(chat_id, test_id)
    
    # Determine role
    if username == VA_bot.lstrip('@'):
        bot_role = "salesperson"
        print(f"\n[SALESPERSON] Message received: {user_message}")
        print(f"[INFO] Chat ID: {chat_id}, Test ID: {test_id}")
    else:
        bot_role = "customer"
        print(f"[CUSTOMER] {user_message}")
    
    # Save incoming salesperson message to database immediately
    insert_message(
        conversation_id=test_id,
        role=bot_role,
        text=user_message,
        chat_id=chat_id,
        bot_name=BOT_NAME if bot_role == "customer" else username
    )
    
    # If message is from salesperson, queue it
    if bot_role == "salesperson":
        # Add message to queue
        message_queue[chat_id].append({
            'message': user_message,
            'test_id': test_id,
            'username': username,
            'message_id': update.message.message_id  # Capture message ID for referencing
        })
        
        queue_size = len(message_queue[chat_id])
        print(f"[QUEUE] Added to queue. Total queued: {queue_size}")
        
        # Cancel existing timer if any
        if chat_id in processing_timers:
            processing_timers[chat_id].cancel()
            print(f"[TIMER] Reset timer (new message received)")
        
        # Start NEW 15-second timer
        processing_timers[chat_id] = asyncio.create_task(
            process_batch_responses(chat_id, context)
        )
        print(f"[TIMER] Started 15-second countdown...")


async def gpt_customer_response(salesperson_message, chat_id):
    """Generate customer response using GPT"""
    conv_history = get_or_create_conversation_history(chat_id, get_latest_test_id())
    
    # Add salesperson message to conversation history
    conv_history['messages'].append({
        "role": "user",
        "content": salesperson_message
    })
    
    try:
        response = client.chat.completions.create(
            model="ft:gpt-3.5-turbo-0125:personal:your-fine-tuned-model-name:Cvi4Yd6v",
            messages=conv_history['messages'],
            temperature=0.85,
            max_tokens=50,
            top_p=0.92,
            frequency_penalty=0.5,
            presence_penalty=0.5,
            stop=["Salesperson:", "Sales person:", "Agent:", "SALESPERSON:"]
        )
        
        customer_response = response.choices[0].message.content.strip()
        
        
        # SAFETY CHECK: Detect if model is acting as salesperson
        salesperson_phrases = [
            "how can i help you",
            "what are you looking for",
            "let me show you",
            "welcome to our store",
            "can i assist you",
            "what brings you in today",
            "are you looking for anything specific",
            "how may i help",
            "what can i do for you"
        ]
        
        response_lower = customer_response.lower()
        
        if any(phrase in response_lower for phrase in salesperson_phrases):
            print("[WARNING] Detected salesperson behavior, regenerating response...")

            # Add reinforcement to force the correct customer behavior
            conv_history['messages'].append({
                "role": "system",
                "content": f"CRITICAL REMINDER: YOU ARE THE CUSTOMER, NOT THE SALESPERSON. You came here to buy {conv_history['product']}. Express what YOU need or ask questions about the product YOU want to buy. Do NOT offer help or ask what the salesperson is looking for!"
            })

            # Regenerate response to ensure customer behavior
            response = client.chat.completions.create(
                model="ft:gpt-3.5-turbo-0125:personal:your-fine-tuned-model-name:Cvi4Yd6v",
                messages=conv_history['messages'],
                temperature=0.85,
                max_tokens=150,
                top_p=0.92,
                frequency_penalty=0.5,
                presence_penalty=0.5,
                stop=["Salesperson:", "Sales person:", "Agent:", "SALESPERSON:"]
            )

            customer_response = response.choices[0].message.content.strip()

        
        # Add customer response to history
        conv_history['messages'].append({
            "role": "assistant",
            "content": customer_response
        })
        
        return customer_response
        
    except Exception as e:
        print(f"[ERROR] GPT API Error: {e}")
        return "Sorry, I'm having trouble responding right now."


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
    print(f"\n🏠 Room ID: {ROOM_ID}")
    print(f"\nBot will use the latest Test ID from database")
    print(f"⏱️  Wait time: {RESPONSE_DELAY} seconds after last message")
    print(f"📦 Batch mode: All replies sent together")
    print(f"Waiting for /start command...\n")
    
    _bot_application.run_polling(drop_pending_updates=True, poll_interval=1)


if __name__ == '__main__':
    main()
