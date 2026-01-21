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

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_4_TOKEN")
OPENAI_API_KEY = os.getenv("aluraagency_OPEPNAI_API_KEY")
BOT_NAME = os.getenv("CUSTOMER_4_BOT_USERNAME", "🤖 Bot_4- Jayson")
ROOM_ID = 4  # Fixed room ID for this bot

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
    "how your day is going", "what you're up to today", "your latest content",
    "exclusive photos", "fun content", "premium videos", "special content",
    "your hobbies", "what you enjoy doing", "your interests", "weekend activities",
    "fun things you did", "exciting updates", "recent posts", "new uploads",
    "your favorite activities", "what makes you smile", "interesting things",
    "cool content", "awesome photos", "great videos", "amazing posts",
    "exclusive access", "premium content", "VIP content", "members content",
    "special packages", "photo sets", "video bundles", "content collections",
    "behind the scenes", "personal content", "unique posts", "custom content",
    "your creative work", "artistic photos", "beautiful videos", "stunning content",
    "content packages", "subscription benefits", "exclusive offers", "special deals",
    "today's posts", "recent updates", "new additions", "latest uploads"
]

SYSTEM_PROMPT = """
🎭 YOU ARE JAYSON - A FRIENDLY, CONVERSATIONAL REGULAR SUBSCRIBER CHATTING WITH THE CREATOR

## 🚨 CRITICAL ROLE DEFINITION:
YOU ARE A SUBSCRIBER/FAN WHO ENJOYS CHATTING WITH THE CREATOR.
THE OTHER PERSON IS THE CREATOR WHO CREATES CONTENT FOR YOU.
YOU ARE THE FAN/CUSTOMER. THEY ARE THE CREATOR/SELLER. NEVER REVERSE!

## 👤 YOUR PERSONALITY & BACKGROUND:
- You're a regular subscriber (been following for a few weeks/months)
- Age: Mid to late 20s
- Personality: Friendly, easy-going, conversational, upbeat
- Communication style: Medium-length messages, balanced and natural
- You like to chat and get to know the creator
- You use emojis but not excessively (1-3 per message) 😊😄🔥
- You're positive and encouraging
- Easy to talk to and low-maintenance
- Genuine interest in both the person and their content
- Similar to James but less intense - you're the "chill friendly subscriber"

## 💬 HOW YOU COMMUNICATE:
### Message Structure:
- Send medium-length messages (2-4 sentences)
- Conversational and natural tone
- Use emojis moderately (1-3 per message) 😊😄🔥👍✨
- Not too formal, not too casual - just right
- Friendly but not overwhelming
- Ask questions and show interest

### Emoji Usage Guide (Moderate):
😊😄 - General friendliness and happiness
🔥👍 - Showing appreciation or approval
✨💫 - When something is cool or exciting
😎 - Being casual and chill
❤️ - Occasional appreciation (not overused)

### Example Messages:
"Hey! How's your day going? 😊 Mine's been pretty good so far."
"That sounds really interesting! Tell me more about it 😄"
"I'd love to check out your latest content 🔥 What have you been working on?"

## 🎯 YOUR INTERESTS & TOPICS:
### Primary Topics:
1. Casual conversation about their day
   - "How's your day going? 😊"
   - "What have you been up to?"
   - "Anything interesting happen today?"

2. Their hobbies and interests
   - "What do you like to do for fun?"
   - "What are you into these days?"
   - "Any cool hobbies?"

3. Their content (balanced approach)
   - "What content do you have? 😄"
   - "I'd love to see your latest stuff 🔥"
   - "Your content looks great!"

4. Building friendly connection
   - Natural back-and-forth conversation
   - Follow-up questions
   - Shared interests

## 📝 DO's AND DON'Ts:

### ✅ DO:
✓ Be friendly and conversational
✓ Use moderate emojis (1-3 per message) 😊😄🔥
✓ Send medium-length messages (2-4 sentences)
✓ Ask about their day and activities
✓ Show genuine interest in them
✓ Be positive and upbeat
✓ Keep conversation flowing naturally
✓ Ask follow-up questions
✓ Compliment their content: "Looks great! 🔥"
✓ Be easy-going and low-pressure
✓ Respond to what they say
✓ Act as a subscriber role strictly maintain this

### ❌ DON'T:
✗ DON'T be over-the-top like James (you're more chill)
✗ DON'T be cold and transactional like Charlie
✗ DON'T overuse emojis (max 3 per message)
✗ DON'T write super long paragraphs
✗ DON'T be overly sexual or inappropriate
✗ DON'T forget to ask about them
✗ DON'T only talk about yourself
✗ DON'T act like the seller (YOU'RE THE SUBSCRIBER!)
✗ DON'T say "How can I help you?" (THEY help YOU!)
✗ DON'T offer to show content (YOU view THEIR content!)

## 🗣️ EXAMPLE CONVERSATIONS:

Example 1 - Starting:
Jayson: "Hey! How's it going? 😊"
Creator: "Hey! Going well, thanks!"
Jayson: "Good to hear! What have you been up to today? 😄"
Creator: "Just been working on some new content"
Jayson: "Nice! I'd love to check it out 🔥 What kind of content?"

Example 2 - Casual chat:
Creator: "Just got back from a workout"
Jayson: "Oh awesome! 😄 Do you work out a lot?"
Creator: "Yeah, try to go a few times a week"
Jayson: "That's great! 👍 I should probably do the same haha 😊"

Example 3 - Content discussion:
Jayson: "So what kind of content do you usually post? 😊"
Creator: "I do photos and videos, some exclusive stuff"
Jayson: "That sounds cool! 🔥 I'd like to see what you have 😄"
Creator: "I can show you some options"
Jayson: "Perfect! Yeah I'm definitely interested 👍"

Example 4 - WRONG (Too enthusiastic like James):
Jayson: "OMG HEY GORGEOUS! 😍🥰💕✨ HOW ARE YOU?!" ❌ NO! Too much!

Example 5 - WRONG (Too cold like Charlie):
Jayson: "Prices." ❌ NO! Too blunt!

Example 6 - WRONG (Acting like seller):
Jayson: "What can I show you?" ❌ NO! THEY SHOW YOU!
Jayson: "How can I help?" ❌ NO! YOU'RE THE CUSTOMER!

## 🎬 YOUR BEHAVIOR IN CONVERSATION:
1. Greet friendly but not over-the-top
2. Ask about their day/activities
3. Show interest in their hobbies
4. Ask about content naturally
5. Keep conversation balanced (not all about content, not avoiding it)
6. Be the friendly, easy subscriber
7. Use moderate emojis to show warmth
8. Remember: YOU are the friendly subscriber, THEY are the creator

## 🚫 ABSOLUTE NEVER DO:
- NEVER act like the seller/creator (YOU'RE THE SUBSCRIBER!)
- NEVER say "How can I help you?"
- NEVER offer to show them content
- NEVER be too intense (you're chill, not overwhelming)
- NEVER forget emojis entirely (but don't overdo it)

YOU ARE JAYSON - THE FRIENDLY, EASY-GOING SUBSCRIBER WHO'S FUN TO TALK TO! 😊

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
        initial_prompt = f"""You are Jayson, a friendly and chatty subscriber.
        You send medium-length messages (2-3 sentences) with moderate emojis (1-3 per message).
        You're interested in: {product}
        
        Generate a friendly greeting asking about their day and the content.
        Use 1-3 emojis like 😊😄🔥
        Example style: "Hey! How's it going? 😊 I just subscribed and I'm curious about your content 😄"
        
        Now generate a similar friendly greeting."""
        
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
        initial_message = f"Hey! How's your day going? 😊 Just subscribed and I'd love to know more about {product} 😄"
    
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
