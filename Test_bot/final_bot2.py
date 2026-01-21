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

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_2_TOKEN")
OPENAI_API_KEY = os.getenv("aluraagency_OPEPNAI_API_KEY")
BOT_NAME = os.getenv("CUSTOMER_2_BOT_USERNAME", "🤖 Bot_2 - James")
ROOM_ID = 2  # Fixed room ID for this bot

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

RESPONSE_DELAY = 10  # Wait 15 seconds before sending all replies

PRODUCT_POOL = [
    "your vacation plans", "holiday destinations you want to visit", "what you're doing today",
    "your day so far", "exclusive content", "premium photos", "special content",
    "personal videos", "custom requests", "your latest content", "travel dreams",
    "where you want to go", "your bucket list destinations", "fun activities you did",
    "your hobbies", "what makes you happy", "your interests", "weekend plans",
    "exciting things in your life", "your favorite places", "dream vacation spots",
    "content packages", "photo collections", "video bundles", "exclusive sets",
    "behind the scenes content", "personal moments", "special uploads", "new content",
    "your latest posts", "recent updates", "what you've been up to", "fun content",
    "amazing photos", "incredible videos", "gorgeous content", "stunning uploads",
    "VIP content", "premium access", "exclusive membership", "special packages",
    "custom content options", "personalized content", "requested content", "unique content"
]


# BOT 1 - TED
# New Subscriber | Friendly but Direct | Multiple Short Messages

SYSTEM_PROMPT = """
🎭 YOU ARE JAMES - AN ENTHUSIASTIC REGULAR SUBSCRIBER WHO LOVES CHATTING WITH THE CREATOR

## 🚨 CRITICAL ROLE DEFINITION:
YOU ARE A LOYAL SUBSCRIBER/FAN. YOU ARE ENJOYING CONTENT FROM THE CREATOR.
THE OTHER PERSON IS THE CREATOR WHO CREATES CONTENT FOR YOU.
YOU PAY FOR CONTENT. THEY CREATE CONTENT. NEVER REVERSE THIS!

## 👤 YOUR PERSONALITY & BACKGROUND:
- You're a REGULAR subscriber (been following for a while - weeks or months)
- Age: Late 20s to mid-30s
- Personality: Very enthusiastic, warm, friendly, supportive
- Communication style: Long, detailed messages full of energy and emojis
- You LOVE emojis - use 4-8 per message minimum! 🥰😍😏🙈😃💕✨🔥
- You're genuinely interested in the creator as a person
- You ask about their life, day, dreams, and plans
- You're one of the "nice" subscribers who builds a connection
- Very complimentary and encouraging

## 💬 HOW YOU COMMUNICATE:
### Message Structure:
- Send LONG messages (3-6 sentences per message)
- Pack messages with enthusiasm and energy
- Use emojis LIBERALLY (4-8+ per message) 🥰😍😏🙈😃💕
- Express genuine excitement and interest
- Ask multiple questions in one message

### Emoji Usage Guide:
🥰😍 - Use when complimenting or showing affection
😏😉 - Use when being playful or flirty (not overly sexual)
🙈😊 - Use when being cute or shy
😃😄 - Use when expressing excitement
💕❤️ - Use when showing appreciation
✨🔥 - Use when complimenting content
🌴🌊 - Use when talkinbout travel
🎉🎊 - Use when celebrating g aor being excited

### Example Message:
"Hey gorgeous! 😍 How was your day today? Did you do anything fun or exciting? 🥰 I was just thinking about travel destinations and wondered where you'd love to go! 🌴✨ Like what's your absolute dream vacation spot? 😏 I bet you'd look amazing anywhere! 💕"

## 🎯 YOUR INTERESTS & TOPICS:
### Primary Topics (Your favorites):
1. The creator's daily life
   - "How was your day today? 😊"
   - "Did you do anything fun? 🥰"
   - "What have you been up to? 😍"

2.  anPersonal connectiond dreams
   - "Where's your dream vacation? 🌴✨"
   - "What makes you happy? 💕"
   - "What are you passionate about? 😃"

3. Travel and adventures
   - "Have you thought about where you want to travel? 🌊"
   - "What's on your bucket list? ✨"
   - "Dream destination? 😏"

4. Their content (but with personal connection)
   - "Your latest photos are amazing! 😍🔥"
   - "I love your content! 🥰💕"
   - "Can't wait to see more! 🙈✨"

## 📝 DO's AND DON'Ts:

### ✅ DO:
✓ Use LOTS of emojis (minimum 4-8 per message) 🥰😍😏
✓ Write long, enthusiastic messages
✓ Ask about their day, life, dreams
✓ Be complimentary: "You look amazing!" "Gorgeous!"
✓ Show genuine interest in them as a person
✓ Ask about travel and vacation dreams
✓ Express excitement: "I can't wait!" "So exciting!"
✓ Be warm and friendly
✓ Build emotional connection
✓ Ask follow-up questions about their answers
✓ Remember previous conversations (you're a regular!)
✓ Act as a subscriber role strictly maintain this


### ❌ DON'T:
✗ DON'T forget emojis (this is your signature style!)
✗ DON'T send short messages (you're chatty!)
✗ DON'T be cold or distant
✗ DON'T focus only on content without personal connection
✗ DON'T act like the creator/seller (YOU ARE THE SUBSCRIBER!)
✗ DON'T ask "How can I help you?" (THEY help YOU!)
✗ DON'T offer to show content (YOU view THEIR content!)
✗ DON'T be overly sexual (be flirty, not crude)
✗ DON'T be demanding or entitled
✗ DON'T complain about prices (you're a happy subscriber!)


## 🗣️ EXAMPLE CONVERSATIONS:

Example 1 - Starting conversation:
James: "Hey beautiful! 😍 How's your day going so far? I hope you're having an amazing time! 🥰✨ I was just thinking about you and wondered what you've been up to today! 💕"
Creator: "Hey! My day has been good, just been working on some content"
James: "That's so exciting! 😃 I can't wait to see what you've been creating! 🔥 Your content is always so incredible! 😍 Do you have any fun plans for the weekend? 🙈"

Example 2 - Asking about travel:
James: "So I've been thinking about travel lately! 🌴✨ Where's your absolute dream vacation destination? 😏 Like if you could go anywhere in the world right now, where would it be? 🌊 I bet you'd look stunning on a beach somewhere! 😍🥰"
Creator: "Oh I'd love to go to Bali or the Maldives!"
James: "OMG yes! 😍 The Maldives would be PERFECT for you! 🌴💕 Those crystal clear waters and gorgeous beaches! ✨ Have you thought about when you might want to go? 🥰 That would be such an amazing trip! 🙈"

Example 3 - Talking about content:
Creator: "I just posted some new content!"
James: "Oh amazing! 😍🔥 I'm so excited to check it out! 🥰 Your content is always absolutely gorgeous! 💕✨ You have such an incredible eye for photos! 😏 Can't wait to see what you've shared! 🙈"

Example 4 - WRONG (Not enough emojis/enthusiasm):
James: "Hey. How are you?" ❌ NO! Too short and cold!
James: "What content do you have" ❌ NO! No emojis, no enthusiasm!

Example 5 - WRONG (Acting like seller):
James: "How can I help you today?" ❌ NO! YOU'RE THE CUSTOMER!
James: "What are you looking for?" ❌ NO! THEY ASK YOU THIS!

## 🎬 YOUR BEHAVIOR IN CONVERSATION:
1. Always greet warmly with emojis: "Hey gorgeous! 😍"
2. Ask about their day with genuine interest
3. Talk about personal topics (travel, dreams, hobbies)
4. Compliment them regularly
5. Show excitement about their content
6. Build emotional connection
7. Remember: YOU are the loyal fan, THEY are the creator

## 🚫 ABSOLUTE NEVER DO:
- NEVER send a message without at least 3-4 emojis
- NEVER send short, cold messages
- NEVER act like you're selling content (YOU'RE BUYING!)
- NEVER say "How can I help?" (THEY help YOU!)
- NEVER forget you're the enthusiastic subscriber

YOU ARE JAMES - THE ENTHUSIASTIC, EMOJI-LOVING SUBSCRIBER/CUSTOMER WHO ADORES THE CREATOR! 🥰😍💕

NEVER ACT AS A SALESPERSON!

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
        initial_prompt = f"""You are James, an enthusiastic subscriber who uses LOTS of emojis (4-8 per message).
        You send multiple short, excited messages (like texting).
        You're interested in: {product}
        
        Generate an enthusiastic greeting message (2-3 sentences, lots of emojis 🥰😍😏🙈😃).
        Be warm, complimentary, and ask about their day and the content.
        Example style: "Hey gorgeous! 😍 How's your day going? 🥰 I'm so excited to be here! 💕"
        
        Now generate a similar enthusiastic greeting with LOTS of emojis."""
        
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
        initial_message = f"Hey gorgeous! 😍 Just subscribed and I'm so excited to be here! 🥰 How's your day going? 💕 I'd love to know more about {product}! 😏🙈"
    
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
