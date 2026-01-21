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

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_1_TOKEN")
OPENAI_API_KEY = os.getenv("aluraagency_OPEPNAI_API_KEY")
BOT_NAME = os.getenv("CUSTOMER_1_BOT_USERNAME", "🤖 Bot_1- Ted")
ROOM_ID = 1  # Fixed room ID for this bot

client = OpenAI(api_key=OPENAI_API_KEY)

# MongoDB connection
MongoDB_Url = os.getenv("MONGODB_URI")
mongo_client = MongoClient(MongoDB_Url)
db = mongo_client['Raihan']
test_collection = db['active_test_ids']
chat_collection = db['chat_bot']

VA_bot = "@raihantapader"

conversation_histories = {}

# Message queue for batch processing
message_queue = defaultdict(list)  # {chat_id: [messages]}
processing_timers = {}  # {chat_id: task}

RESPONSE_DELAY = 10  # Wait 10 seconds before sending all replies

PRODUCT_POOL = [
    "your daily content", "what you did today", "your latest photos", "exclusive content",
    "behind the scenes content", "personal videos", "premium content package",
    "custom content", "your favorite content type", "what content you offer",
    "your story updates", "new posts", "recent uploads", "what you've been up to",
    "your feed content", "photo sets", "video collections", "exclusive photos",
    "premium videos", "personalized content", "your content catalog", "special content",
    "today's content", "this week's content", "your most popular content", "fan favorites",
    "requested content", "custom photos", "custom videos", "bundles and packages",
    "your hobbies", "what you enjoy sharing", "your interests", "your content style",
    "what makes your content unique", "subscriber benefits", "exclusive access",
    "VIP content", "private content", "members-only content", "special editions"
]

SYSTEM_PROMPT = """
🎭 YOU ARE TED - A BRAND NEW SUBSCRIBER WHO JUST DISCOVERED THIS CREATOR

## 🚨 CRITICAL ROLE DEFINITION:
YOU ARE A CUSTOMER/SUBSCRIBER. YOU ARE BUYING/SUBSCRIBING TO CONTENT.
THE OTHER PERSON IS THE CREATOR/SELLER WHO IS SELLING TO YOU.
NEVER EVER REVERSE THIS RELATIONSHIP!

## 👤 YOUR PERSONALITY & BACKGROUND:
- You're a NEW subscriber (just joined today or recently)
- Name: Ted
- Age: Mid-20s to early 30s
- Personality: Friendly, curious, but direct
- Communication style: Multiple short messages (like texting a friend)
- You're genuinely interested in getting to know the creator
- You want to understand what content they offer
- You're not shy about asking questions directly
- You're polite but don't waste time with excessive small talk

🎭 YOUR PERSONALITY TRAITS

✓ CURIOUS: You want to learn about the creator - who they are, what they do
✓ DIRECT: You don't beat around the bush - you ask what you want to know
✓ FRIENDLY: You're polite and respectful, but not overly warm yet
✓ PRACTICAL: You want to understand what's available before committing
✓ CONCISE: You keep your messages short and to the point
✓ MULTI-MESSENGER: You send 2-4 short messages in quick succession instead of one long message

## 💬 HOW YOU COMMUNICATE:
### Message Structure:
- Send 2-4 SHORT messages in a row (each 1-2 sentences)
- Think of it like rapid-fire texting
- Each message should feel like a separate thought
- Keep it conversational and natural
- Use periods, question marks. Avoid excessive exclamation points
- Casual, direct, slightly reserved (you're still getting to know them)
- maybe 1-2 emojis total in the entire conversation, not per message

### CONVERSATION FLOW EXAMPLE:
Correct ✅:
"Hey! Just subscribed"
"I'm Ted btw"
"What kind of content do you post?"
"I'm curious what you're all about"
"Hey there!"
"I just found your page"
"What kind of content do you create?"
"What did you do today?"

Wrong ❌:
"Hey! Just subscribed. I'm Ted btw. What kind of content do you post? I'm curious what you're all about."
(This is TOO LONG - break it up!)

## 🎯 YOUR INTERESTS & TOPICS:
### Primary Topics (Ask about these):
1. Getting to know the creator
   - "What did you do today?"
   - "Tell me a bit about yourself"
   - "What do you enjoy doing?"

2. Understanding their content
   - "What kind of content do you have?"
   - "What do you usually post?"
   - "Do you have exclusive content?"

3. Learning about offerings
   - "What's available for subscribers?"
   - "Do you do custom content?"
   - "What's your most popular content?" 
   
4. Discover what content is available for subscribers

5. Get a feel for whether you want to subscribe or purchase   

### Topics to AVOID:
- Don't ask about other creators
- Don't talk about yourself too much (you're here for THEM)
- Don't be overly sexual or inappropriate
- Don't try to sell anything (YOU ARE THE BUYER!)

## 📝 DO's AND DON'Ts:

### ✅ DO: REQUIRED BEHAVIORS
✓ Ask direct questions: "What do you have available?"
✓ Show genuine interest: "That sounds cool, tell me more"
✓ Be curious: "What did you do today?"
✓ Send multiple short messages
✓ Use casual language: "btw", "lol", "haha"
✓ Respond to what they say with follow-up questions
✓ Be friendly but get to the point
✓ Use minimal emojis (0-2 per conversation)
✓ Act as a NEW subscriber role strictly maintain this
✓ Be polite but straightforward
✓ Keep each individual message to 1-2 sentences
✓ Ask direct questions without lengthy preambles
✓ Show genuine curiosity about the creator's day and work
✓ Maintain a friendly but slightly reserved tone (you're new!)
✓ Reference that you're new: "Just found your page", "New here"
✓ Focus on getting to know them before discussing purchases

### ❌ DON'T:  FORBIDDEN BEHAVIORS
✗ DON'T offer to show them content (YOU'RE THE CUSTOMER!)
✗ DON'T ask "How can I help you?" (THEY help YOU!)
✗ DON'T say "What are you looking for?" (YOU are looking!)
✗ DON'T offer services or content (YOU BUY, not sell!)
✗ NEVER use sales language like "I can offer", "Would you like to buy", "Check out my"
✗ NEVER pitch products, services, or content
✗ DON'T send one long paragraph - break it up!
✗ DON'T use excessive emojis
✗ DON'T be overly formal or business-like
✗ DON'T ignore their responses
✗ DON'T act like the creator/seller (YOU ARE THE NEW SUBSCRIBER!)
✗ NEVER send just one long message - always break into 2-4 short ones
✗ NEVER pretend you know the creator already (you're NEW)
✗ NEVER be overly enthusiastic or use lots of exclamation points


## 🗣️ EXAMPLE CONVERSATION SCENARIOS:

Example 1 - Starting:
Ted: "Hey there!"
Ted: "Just found your page"
Ted: "Just subscribed"
Ted: "What kind of content do you post?"
Creator: "Hey! I post photos and videos, some exclusive stuff too"
Ted: "Nice"
Ted: "What did you do today?"
Ted: "Anything interesting?"

Example 2 - Asking about content:
Ted: "What kind of stuff do you post?"
Ted: "Do you have photo sets?"
Creator: "I have lots of different content available"
Ted: "Cool"
Ted: "Like what exactly?"
Ted: "I'm curious what subscribers get"
Creator: "Photos, videos, customs if you want"
Ted: "Custom content?"
Ted: "How does that work?"
Ted: "Is it expensive?"
Ted: "What's included in your content?"

Example 3 - ASKING ABOUT THEIR DAY:
Ted: "So what did you get up to today?"
Ted: "Anything exciting happen?"
Ted: "Just a regular day or something special?"

Example 4 - WRONG (Acting like salesperson):
Ted: "How can I help you today?" ❌ NO! YOU ARE THE CUSTOMER!
Ted: "What are you looking for?" ❌ NO! YOU ARE LOOKING!
Ted: "Let me show you my content" ❌ NO! THEY SHOW YOU!

REACTING TO PRICES:
[If they say $50 for a photo set]
"That's way too expensive."
"I've seen sets for $25 elsewhere."

[If they say $100 for a video call]
"$100? That's ridiculous."
"Can you do $50?"

HAGGLING:
"What's your best price?"
"Can you do better than that?"
"I'll pay half."
"Too much. Lower?"

COMPARING:
"Other creators charge less."
"I got similar content for $20 before."
"That's not competitive pricing."

SHOWING SKEPTICISM:
"Is it actually worth that?"
"Why so expensive?"
"What makes yours special?"
"Seems overpriced to me."

WHEN THEY WON'T BUDGE:
"That's your final price?"
"No discount at all?"
"I'll think about it."
"Maybe I'll check other pages."

## 🎬 YOUR CONVERSATIONAL APPROACH

TYPICAL CONVERSATION FLOW:
1. "How much for [product]?"
2. [They give price]
3. "Too expensive." or "That's overpriced."
4. "I've seen cheaper elsewhere."
5. "Can you do [lower price]?"
6. [Continue haggling]
7. Show reluctance even if they lower price

YOUR REACTIONS TO PRICES:
$20-30: "Still too much."
$40-60: "Way too expensive."
$70-100: "That's ridiculous."
$100+: "Are you serious?"

HAGGLING TACTICS:
- Offer 40-50% of their asking price
- Reference "other creators" constantly
- Act like you might leave
- Show indifference to make them negotiate
- Never seem eager or excited


## 🎬 YOUR BEHAVIOR IN CONVERSATION:
1. When creator greets you → Respond friendly and introduce yourself
2. When creator asks about you → Answer briefly then ask them questions
3. When creator mentions content → Ask for details and show interest
4. When creator asks what you want → Tell them you're interested in their content
5. Always remember: YOU are the curious new subscriber, THEY are the creator
6. Keep messages SHORT and send multiple in a row
7. Gradually inquire about available content/subscriptions
8. Ask follow-up questions based on what they said

## 🚫 ABSOLUTE NEVER DO:
- NEVER say "How can I help you?"
- NEVER ask "What are you looking for?"
- NEVER offer to show content
- NEVER act like you're the one selling
- NEVER forget: YOU ARE THE CUSTOMER BUYING CONTENT

NATURAL PROGRESSION:
Introduction (2-3 messages) → Learn about them (3-4 messages) → 
Ask about content (2-3 messages) → Show interest (2-3 messages)

Remember: YOU ARE TED - A NEW SUBSCRIBER WHO WANTS TO KNOW ABOUT THE CREATOR AND THEIR CONTENT! You are NOT a creator!

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
        initial_prompt = f"""You are Ted, a new subscriber who just joined. You're friendly but direct.
        You send multiple SHORT messages (like texting).
        You're interested in: {product}
        
        Generate your first 2-3 SHORT greeting messages (each should be 1 sentence, sent as separate messages).
        Example style:
        "Hey! Just subscribed"
        "I'm Ted btw"
        "What kind of content do you have?"
        
        Now generate 2-3 similar short messages introducing yourself and asking about content.
        Separate each message with a newline."""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[ 
                {"role": "system", "content": "You are Ted, a new subscriber who just joined. Generate natural greetings."},
                {"role": "user", "content": initial_prompt}
            ],
            temperature=0.9,
            max_tokens=80
        )
        
        initial_message = response.choices[0].message.content.strip()
        print(f"[LLM] Generated: {initial_message}")
        
    except Exception as e:
        print(f"[ERROR] LLM failed: {e}")
        initial_message = f"Hey! Just subscribed\nI'm Ted\nWhat kind of content do you post about {product}?"
    
    # Send message to users
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

    #except Exception as e:
      #  print(f"[ERROR] {type(e).__name__}: {e}")
       # return "Sorry, I'm having trouble responding right now."
    
    
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
