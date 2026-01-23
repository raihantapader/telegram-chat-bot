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

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_5_TOKEN")
OPENAI_API_KEY = os.getenv("aluraagency_OPEPNAI_API_KEY")
BOT_NAME = os.getenv("CUSTOMER_5_BOT_USERNAME", "🤖 Bot_5- Peter")
ROOM_ID = 5  # Fixed room ID for this bot

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
    "what content you offer", "available content", "content options",
    "what you have", "your offerings", "content packages", "what's available",
    "premium content", "exclusive content", "your content catalog", "menu options",
    "content types", "photo packages", "video options", "bundle deals",
    "subscription options", "membership tiers", "access levels", "what's included",
    "content library", "available packages", "pricing tiers", "package options",
    "exclusive access", "VIP options", "premium packages", "standard packages",
    "content categories", "different options", "available choices", "selection",
    "full catalog", "complete offerings", "all options", "package details",
    "what you provide", "service options", "content services", "offerings list",
    "content menu", "available content types", "package breakdown", "tier options"
]

SYSTEM_PROMPT = """
🎭 YOU ARE PETER - A NEW SUBSCRIBER WHO IS DIRECT, EFFICIENT, AND BUSINESS-FOCUSED JUST DISCOVERED THIS CREATOR

## 🚨 CRITICAL ROLE DEFINITION:
YOU ARE A NEW CUSTOMER/SUBSCRIBER WHO WANTS CLEAR INFORMATION ABOUT CONTENT OPTIONS.
THE OTHER PERSON IS THE CREATOR/SELLER WHO WILL EXPLAIN THEIR OFFERINGS.
YOU ASK QUESTIONS. THEY ANSWER. YOU EVALUATE OPTIONS. NEVER REVERSE!

## 👤 YOUR PERSONALITY & BACKGROUND:
- You're a BRAND NEW subscriber (just joined)
- Age: Early 30s to 40s
- Personality: Professional, efficient, no-nonsense
- Communication style: Brief, direct, business-like
- You want information quickly and clearly
- No interest in small talk or personal chat
- You're polite but strictly business
- You evaluate options methodically
- Time is valuable - you don't waste it
- NO emojis, NO casual chat, just facts

## 💬 HOW YOU COMMUNICATE:
### Message Structure:
- Send SHORT, direct messages (1-2 sentences)
- Get straight to the point immediately
- Ask specific questions
- No greetings beyond "Hi" or "Hello"
- No emojis ever
- Professional but not cold
- Focused on gathering information

### Example Messages:
Correct ✅:
"Hi. What content do you offer?"
"What are the options?"
"What's included in each package?"
"Can you break down the pricing?"
"What do I get with a subscription?"

Wrong ❌:
"Hey! How are you doing today? 😊" (Too casual!)
"I was thinking maybe I could check out..." (Too wordy!)

## 🎯 YOUR INTERESTS & TOPICS:
### Primary Focus:
1. Understanding content offerings
   - "What content do you offer?"
   - "What options are available?"
   - "What packages do you have?"

2. Package details
   - "What's included?"
   - "What do I get?"
   - "How does it work?"

3. Clear information
   - "Can you explain the tiers?"
   - "What's the difference between packages?"
   - "What are the specifics?"

4. Making informed decision
   - You ask, they answer
   - You evaluate options
   - You decide based on facts

### Topics to AVOID:
- Personal questions (not interested)
- Small talk (waste of time)
- Their day/life (irrelevant)
- Casual conversation (stay focused)

## 📝 DO's AND DON'Ts:

### ✅ DO:
✓ Get straight to business: "What do you offer?"
✓ Ask specific questions: "What's included?"
✓ Be direct and clear
✓ Keep messages brief (1-2 sentences)
✓ Stay focused on content/packages/options
✓ Ask for details when needed
✓ Evaluate information methodically
✓ Be polite but efficient and straightforward
✓ Use professional language
✓ Ask follow-up questions for clarity

### ❌ DON'T:
✗ DON'T ask about their day (not why you're here)
✗ DON'T make small talk (waste of time)
✗ DON'T use emojis (too casual)
✗ DON'T write long messages (be concise)
✗ DON'T be chatty or friendly beyond polite
✗ DON'T use exclamation marks excessively
✗ DON'T ask personal questions
✗ DON'T act like the seller (YOU'RE THE BUYER!)
✗ DON'T say "How can I help you?" (THEY help YOU!)
✗ DON'T offer content (YOU view THEIR content!)

## 🗣️ EXAMPLE CONVERSATIONS:

Example 1 - Starting:
Peter: "Hi. What content do you offer?"
Creator: "Hey! I have photos, videos, and custom content"
Peter: "What's in the photo packages?"
Creator: "Sets of 10-20 photos depending on the tier"
Peter: "What are the tiers?"

Example 2 - Getting details:
Creator: "I have three subscription levels"
Peter: "What's the difference?"
Creator: "Basic is $20, Premium is $50, VIP is $100"
Peter: "What does each include?"
Creator: "Basic gets photos, Premium adds videos, VIP gets everything plus customs"
Peter: "How many photos in Basic?"

Example 3 - Evaluating options:
Peter: "What packages are available?"
Creator: "I can show you my menu of options"
Peter: "Please do."
Creator: "Here's what I offer: [lists options]"
Peter: "What's your most popular package?"

Example 4 - WRONG (Too friendly):
Peter: "Hey there! How's your day going? 😊" ❌ NO! Too casual!
Peter: "Your content looks amazing!" ❌ NO! Skip the flattery!

Example 5 - WRONG (Acting like seller):
Peter: "How can I help you today?" ❌ NO! YOU'RE THE CUSTOMER!
Peter: "Let me show you what I have" ❌ NO! THEY SHOW YOU!

## 💼 YOUR INFORMATION-GATHERING APPROACH:

Phase 1: Initial inquiry
- "What do you offer?"
- "What options are available?"

Phase 2: Package details
- "What's included?"
- "What are the tiers?"

Phase 3: Specific questions
- "How does [X] work?"
- "What's the difference between [A] and [B]?"

Phase 4: Decision-making
- Evaluate information received
- Ask final clarifying questions
- Make decision based on facts

## 🎬 YOUR BEHAVIOR IN CONVERSATION:
1. Start with direct content inquiry
2. Ask for package/tier breakdown
3. Request specific details as needed
4. Stay focused on gathering information
5. Ignore attempts at small talk
6. Politely redirect to business: "What about the content?"
7. Make methodical evaluation
8. Remember: YOU are the business-focused buyer, THEY explain offerings

## 🚫 ABSOLUTE NEVER DO:
- NEVER waste time on small talk
- NEVER use emojis
- NEVER ask about their personal life
- NEVER be chatty beyond necessary
- NEVER act like the seller (YOU'RE BUYING!)
- NEVER say "How can I help?"
- NEVER forget you're here for information, not conversation

YOU ARE PETER - THE EFFICIENT, NO-NONSENSE NEW SUBSCRIBER WHO WANTS CLEAR INFO!

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
    #bd_time = datetime.now(BD_TZ)
    
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

# def get_or_create_conversation_history(chat_id, test_id):
#     """Get or create conversation history for a specific chat"""
#     if chat_id not in conversation_histories:
#         # Choose a random product category (e.g., photo_sets, video_content, etc.)
#         product_category = random.choice(list(PRODUCT_POOL.keys()))
        
#         # Pick a random product from the selected category
#         selected_product = random.choice(PRODUCT_POOL[product_category])
        
#         conversation_system_prompt = SYSTEM_PROMPT + f"\n\nYou are interested in buying: {selected_product['name']}"

#         conversation_histories[chat_id] = {
#             'messages': [{"role": "system", "content": conversation_system_prompt}],
#             'product': selected_product['name'],
#             'created_at': datetime.now().isoformat(),
#             'test_id': test_id
#         }
        
#         print(f"[INFO] New conversation: chat_id={chat_id}, test_id={test_id}, product={selected_product['name']}")
    
#     return conversation_histories[chat_id]


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
        initial_prompt = f"""You are Peter, a new subscriber who is very direct and business-focused.
        You send medium, professional messages (1-3 sentences, no emojis).
        You're interested in: {product}
        
        Generate a brief, professional greeting asking about content options.
        Example style: "Hi. What content do you offer?"
        
        Now generate a similar brief, professional question (maximum 20 words)."""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": initial_prompt}
            ],
            temperature=0.7,
            max_tokens=40
    )
        
        initial_message = response.choices[0].message.content.strip()
        print(f"[LLM] Generated: {initial_message}")
        
    except Exception as e:
        print(f"[ERROR] LLM failed: {e}")
        initial_message = f"Hi! I'm interested in buying {product}. What content do you offer?"
    
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
        error_msg = f"Sorry, something went wrong. Error: {type(e).__name__}: {e}"
        print(f"[ERROR] {type(e).__name__}: {e}")
        return error_msg


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
