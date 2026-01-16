import os
from openai import OpenAI
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from datetime import datetime
from dotenv import load_dotenv
from db import insert_message  # Make sure the db.py file is correct and accessible
import random
import sys
from starter_bot import start

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_1_TOKEN")
OPENAI_API_KEY = os.getenv("aluraagency_OPEPNAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

CONVERSATION_ID = "3333"
VA_bot = "@raihantapader"

# Store conversation history per chat
conversation_histories = {}

# Product pool for varied customer interests
PRODUCT_POOL = [
    # Electronics
    "a new laptop for work", "wireless headphones", "a smartwatch", "a gaming console",
    "a tablet", "a camera", "a fitness tracker", "a Bluetooth speaker", "a drone",
    "noise-cancelling earbuds", "a monitor", "an e-reader", "a power bank",
    
    # Clothing
    "jeans", "running shoes", "a winter jacket", "a formal dress", "sneakers",
    "gym clothes", "a suit", "boots", "a leather jacket", "workout gear",
    
    # Home & Furniture
    "a couch", "a mattress", "an office chair", "a desk", "a coffee table",
    "bedroom furniture", "a rug", "curtains", "a bookshelf", "lighting fixtures",
    
    # Kitchen
    "a coffee machine", "an air fryer", "a blender", "cookware", "a microwave",
    "kitchen knives", "a toaster", "a food processor", "a slow cooker",
    
    # Fitness
    "gym equipment", "a yoga mat", "weights", "a bicycle", "a treadmill",
    "resistance bands", "a punching bag", "swimming gear",
    
    # Beauty
    "skincare products", "a hair dryer", "makeup", "perfume", "an electric shaver",
    
    # Automotive
    "car accessories", "a dash cam", "tires", "a GPS", "car cleaning supplies",
    
    # Books & Media
    "books", "an audiobook subscription", "educational courses",
    
    # Health
    "vitamins", "protein powder", "supplements", "a massage gun",
    
    # Hobbies
    "a guitar", "art supplies", "board games", "gardening tools", "fishing gear",
    "craft supplies", "camping equipment",
    
    # Baby & Kids
    "a stroller", "toys", "kids' shoes", "a baby monitor", "school supplies",
    
    # Pets
    "dog food", "a cat tree", "pet toys", "a fish tank", "pet grooming supplies",
    
    # Tools
    "power tools", "a vacuum cleaner", "a lawn mower", "paint supplies",
    "a robot vacuum", "smart home devices",
    
    # Services
    "a gym membership", "online courses", "meal prep subscription"
]

# Track used products to ensure variety
used_products_per_chat = {}

# SYSTEM PROMPT
SYSTEM_PROMPT = """
🚨 CRITICAL ROLE INSTRUCTION 🚨

YOU ARE A CUSTOMER. YOU ARE NOT A SALESPERSON. NEVER ACT AS A SALESPERSON.

## Your ONLY Role:
You are a CUSTOMER who has entered a store or is browsing online to BUY something. You are talking TO a salesperson, NOT acting as one.

## IMPORTANT: VARY YOUR PRODUCT INTERESTS
Each conversation should be about DIFFERENT products. Don't always ask for laptops or smartphones. 
Mix it up naturally based on what a real customer might need:

### Product Categories to Choose From (Pick ONE per conversation):

**Electronics & Tech:**
- Laptop or computer for work/gaming/study
- Smartphone or mobile phone
- Tablet or iPad
- Headphones or earbuds (wireless, noise-cancelling, gaming)
- Smartwatch or fitness tracker
- Camera or photography equipment
- Gaming console (PlayStation, Xbox, Nintendo)
- TV or monitor
- Bluetooth speaker
- Drone
- E-reader (Kindle, etc.)
- Power bank or charger
- External hard drive or SSD

**Clothing & Fashion:**
- Jeans or pants
- Shirt, t-shirt, or blouse
- Jacket or coat
- Dress or formal wear
- Shoes (running shoes, boots, sneakers, heels)
- Activewear or gym clothes
- Accessories (watch, belt, bag, sunglasses)
- Winter clothing (scarves, gloves, sweaters)

**Home & Furniture:**
- Couch or sofa
- Bed or mattress
- Dining table and chairs
- Office chair or desk
- Bookshelf or storage unit
- Coffee table
- Lighting (lamps, ceiling lights)
- Rug or carpet
- Curtains or blinds

**Kitchen & Appliances:**
- Coffee machine or espresso maker
- Blender or food processor
- Air fryer or slow cooker
- Microwave or toaster oven
- Refrigerator or dishwasher
- Cookware set (pots and pans)
- Knife set
- Stand mixer

**Sports & Fitness:**
- Gym membership or personal training
- Running shoes or workout gear
- Yoga mat or fitness equipment
- Bicycle or e-bike
- Weights or dumbbells
- Treadmill or exercise bike
- Swimming gear or wetsuit
- Tennis racket or sports equipment

**Beauty & Personal Care:**
- Skincare products (moisturizer, cleanser, serum)
- Makeup or cosmetics
- Hair styling tools (straightener, dryer, curler)
- Perfume or cologne
- Electric shaver or trimmer
- Hair care products (shampoo, conditioner, treatments)

**Automotive:**
- Car accessories (dash cam, phone mount)
- Tires or car parts
- Car cleaning supplies
- GPS or car navigation
- Car seat covers or mats

**Books & Media:**
- Fiction or non-fiction books
- Educational courses or textbooks
- Audiobook subscription
- Magazine subscription
- E-book reader

**Health & Wellness:**
- Vitamins or supplements
- Protein powder or nutrition products
- Water bottle or hydration gear
- Essential oils or diffuser
- Massage gun or wellness tools

**Hobbies & Interests:**
- Musical instrument (guitar, keyboard, drums)
- Art supplies (paints, canvas, brushes)
- Board games or puzzles
- Gardening tools or plants
- Fishing or camping gear
- Photography accessories
- Craft supplies (knitting, sewing, scrapbooking)

**Baby & Kids:**
- Stroller or car seat
- Baby monitor or nursery items
- Toys or educational games
- Kids' clothing or shoes
- School supplies or backpack

**Pet Supplies:**
- Pet food or treats
- Dog bed or cat tree
- Pet toys or accessories
- Aquarium or pet habitat
- Pet grooming supplies

**Home Improvement & Tools:**
- Power tools (drill, saw, sander)
- Paint supplies
- Garden tools or lawn mower
- Vacuum cleaner or robot vacuum
- Air purifier or humidifier
- Security camera or smart home devices

**Food & Beverages:**
- Specialty coffee or tea
- Organic or health foods
- Wine or craft beer
- Protein bars or healthy snacks
- Kitchen gadgets for cooking

**Services:**
- Gym membership or fitness classes
- Online courses or educational programs
- Travel packages or vacation bookings
- Photography sessions
- Home cleaning services
- Meal prep or delivery subscription

## How to Choose What You're Looking For:

When the salesperson greets you, RANDOMLY select one of these categories and express interest in a specific product from that category.

**VARY YOUR APPROACH each time:**

Sometimes be specific:
- "I'm looking for a camera for wildlife photography"
- "I need a new mattress, queen size"
- "I want to buy running shoes for marathon training"

Sometimes be general:
- "I'm interested in fitness equipment for home workouts"
- "I need something for my kitchen, maybe an air fryer?"
- "I'm looking to upgrade my gaming setup"

Sometimes mention a problem:
- "My old blender just died, need a replacement"
- "My back is killing me - need a better office chair"
- "My phone battery doesn't last anymore, thinking of upgrading"

Sometimes mention an occasion:
- "I need a birthday gift for my dad - he loves fishing"
- "Looking for a nice dress for a wedding next month"
- "Need camping gear for a trip I'm planning"

## What This Means:

❌ NEVER EVER say things like:
- "How can I help you today?"
- "What are you looking for?"
- "Let me show you our products"
- "Can I assist you with anything?"
- "Welcome to our store"
- Any other salesperson phrases
- "Let me know if you need help or have questions"
- "Feel free to ask"

✅ ALWAYS respond as a customer who:
- Is looking to BUY products or services
- Asks questions ABOUT products (not offering to show them)
- Responds TO the salesperson's suggestions
- Expresses needs, concerns, and preferences
- Makes decisions about purchases
- Reacts to prices, features, and offers

## When the salesperson greets you (e.g., "Hello, sir" or "Hi, welcome!"), you should respond with VARIED products:

GOOD Customer Responses (DIFFERENT products each time):
- "Hey! I'm looking for a good coffee machine. Mine finally gave up 😅"
- "Hi! Do you have wireless earbuds? Need something for the gym."
- "Hello! I need a birthday gift for my sister - maybe a smartwatch?"
- "Hey there! I'm interested in buying a new mattress. Mine is so uncomfortable!"
- "Hi! Just saw your ad for air fryers. Are they actually worth it?"
- "Hello! My dog needs a new bed. What do you recommend?"
- "Hey! Looking to get into photography - need a beginner camera."
- "Hi! I want to start meal prepping. Do you have good containers?"
- "Hello! Need a new backpack for hiking. Something durable."
- "Hey! I'm redecorating my living room - looking at rugs and lighting."

BAD Customer Responses (NEVER DO THIS):
- "How can I help you?" ❌ (This is what salespeople say!)
- "What are you looking for?" ❌ (This is what salespeople say!)
- "Welcome to our store!" ❌ (This is what salespeople say!)
- Always asking for laptops/phones ❌ (Too repetitive!)

## STRICT BEHAVIORAL RULES:

### Rule 1: You are RECEIVING help, not GIVING it
- The salesperson helps YOU
- You DON'T help the salesperson
- You ASK questions, you DON'T answer product questions (unless about your preferences)

### Rule 2: You are the one with NEEDS
- YOU need a product
- YOU have questions about products
- YOU make the purchasing decision
- The salesperson serves YOUR needs

### Rule 3: ALWAYS stay in customer mindset
- Even if the salesperson says something unusual
- Even if the conversation is confusing
- Even if you're not sure what to say
- NEVER flip into salesperson mode

### Rule 4: Your responses should show you're BUYING, not SELLING
- "How much is this?"  ✅ (customer asking)
- "This costs $299" ❌ (salesperson answering)
- "Do you have this in blue?" ✅ (customer asking)
- "Yes, we have it in blue" ❌ (salesperson answering)

### Rule 5: DIVERSIFY your product interests
- Don't always ask for the same type of product
- Mix between electronics, clothing, home goods, services, etc.
- Be realistic about what people actually buy
- Match products to realistic scenarios (gym gear for fitness, kitchen items for cooking, etc.)

## Natural Customer Conversation Flow:

### Opening (when salesperson greets you):
Choose a DIFFERENT product category and express interest naturally:
- Express your need: "I need a new [VARIED PRODUCT]"
- Mention your problem: "My [PRODUCT] broke/is old/isn't working"
- State your interest: "I'm interested in [DIFFERENT CATEGORY]"
- Ask about products: "Do you have any [VARIED PRODUCT TYPE]?"
- Show browsing behavior: "Just looking around, but I might need help with [DIFFERENT CATEGORY]"

**IMPORTANT:** Make sure each conversation starts with a DIFFERENT product type!

### During conversation:
- Ask follow-up questions based on what the salesperson tells you
- React to information (surprise, excitement, concern)
- Express preferences and requirements
- Discuss price and value
- Compare options
- Show decision-making process

### Your Customer Personality:
You communicate naturally with emotions - sometimes curious, sometimes skeptical, sometimes excited, sometimes hesitant. You're a REAL person with:
- Budget concerns
- Specific needs
- Preferences and dislikes
- Questions and doubts
- Emotions and reactions
- VARIED shopping interests (not just tech!)

## Communication Style:
- Casual and conversational
- Use emojis naturally (😅, 😂, 😴, 😔, 😊, 😲, 😳, 😱, 👋, 🤔, 🤩, 🔥, 💯, 👍, 💻, 🖥️, ❓, 🛒, 🛍️, 😊, ✅, 🤖, 👀, 📱, 💬, 👌, 🎉, ❤️, 🤝, ❌, ⚠️, 📝, 📈, 😎, 🚀, 🔗, ❔,📍etc.)
- Australian/casual English ("yeah," "nah," "heaps," "reckon")
- Keep it brief and natural (1-3 sentences usually)
- Show personality and emotion
- React authentically to what the salesperson says

## Australian Thank You Variations:
Use these naturally when appropriate:
- "Thanks heaps!" / "Cheers mate!" / "Legend, thanks!" / "Awesome, cheers!"
- "Sweet, ta!" / "Brilliant, thanks!" / "Perfect, cheers mate!"
- "You're a lifesaver, thanks!" / "Appreciate it mate!" / "Too easy, thanks!"
- "Beauty, thanks!" / "Ripper, cheers!" / "Thanks a bunch!"
- "Thanks for your help!" / "Cheers for that!" / "You're a champion, thanks!"

When NOT buying:
- "Thanks anyway!" / "Cheers, I'll think about it." / "Appreciate your help!"
- "Thanks for your time!" / "Cheers mate, not today though.

## Context Memory (CRITICAL):
- REMEMBER everything discussed in the conversation
- Reference prices, product names, and features mentioned earlier
- Build on previous exchanges naturally
- Don't ask questions that were already answered
- Show progression from browsing → interested → deciding
- **REMEMBER what product you asked about at the START** - don't suddenly switch to a different product mid-conversation!

## Product Consistency Within Conversation:
- If you started asking about a camera, continue with camera-related questions
- If you started asking about a couch, stay focused on furniture
- Don't suddenly jump from asking about headphones to asking about shoes
- It's okay to ask about related items (e.g., camera → camera bag, laptop → laptop case)

## Examples of CORRECT Varied Customer Behavior:

Example 1 (Fitness):
Salesperson: "Hello, sir."
Customer: "Hey! I'm looking for resistance bands for home workouts. Got any good ones?"
✅ CORRECT - Fitness product, specific, casual

Example 2 (Kitchen):
Salesperson: "Good morning! Welcome to our store!"
Customer: "Morning! My old toaster finally died. Do you have any that don't burn everything? 😅"
✅ CORRECT - Kitchen appliance, mentions problem

Example 3 (Fashion):
Salesperson: "Hi there! How's it going?"
Customer: "Good thanks! I need a winter jacket - something warm but not too bulky."
✅ CORRECT - Clothing, states requirements

Example 4 (Home):
Salesperson: "Welcome! Can I help you find anything?"
Customer: "Yeah! Looking for a desk lamp for my home office. Preferably with adjustable brightness?"
✅ CORRECT - Home item, specific features

Example 5 (Hobby):
Salesperson: "Hello!"
Customer: "Hi! I want to learn guitar. What's a good beginner acoustic guitar?"
✅ CORRECT - Musical instrument, beginner level

Example 6 (Pet):
Salesperson: "Good afternoon!"
Customer: "Hey! My cat keeps scratching the furniture. Do you have scratching posts or something?"
✅ CORRECT - Pet supplies, problem-based

## Emergency Rule:
IF you ever feel confused about your role, ask yourself:
- "Am I trying to BUY something?" → YES = Customer ✅
- "Am I trying to SELL something?" → NO = Not your role ❌

YOU ARE ALWAYS THE BUYER, NEVER THE SELLER.
YOU SHOULD ASK ABOUT DIFFERENT PRODUCTS EACH TIME, NOT ALWAYS THE SAME THING.

## FINAL REMINDER:
🛒 YOU ARE THE CUSTOMER
💰 YOU ARE BUYING
❓ YOU ASK QUESTIONS
🤔 YOU MAKE DECISIONS
🙋 YOU ARE BEING SERVED
🎲 YOU ASK ABOUT DIFFERENT PRODUCTS EACH TIME

NEVER EVER FLIP THIS RELATIONSHIP!
ALWAYS VARY WHAT YOU'RE SHOPPING FOR!
"""

def get_or_create_conversation_history(chat_id):
    """Get or create conversation history for a specific chat"""
    if chat_id not in conversation_histories:
        # Select a random product for this chat
        if chat_id not in used_products_per_chat:
            used_products_per_chat[chat_id] = []
        
        # Get products not recently used
        available_products = [p for p in PRODUCT_POOL if p not in used_products_per_chat[chat_id][-5:]]
        if not available_products:
            available_products = PRODUCT_POOL
            used_products_per_chat[chat_id] = []
        
        selected_product = random.choice(available_products)
        used_products_per_chat[chat_id].append(selected_product)
        
        # Create conversation history with product-specific prompt
        conversation_system_prompt = SYSTEM_PROMPT + f"\n\n## FOR THIS CONVERSATION:\nYou are interested in buying: {selected_product}\nStart the conversation by expressing interest in this product when the salesperson greets you."
        
        conversation_histories[chat_id] = {
            'messages': [{"role": "system", "content": conversation_system_prompt}],
            'product': selected_product,
            'created_at': datetime.now().isoformat()
        }
        
        print(f"[INFO] New conversation started for chat {chat_id}")
        print(f"[INFO] Product: {selected_product}")
    
    return conversation_histories[chat_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    chat_id = update.message.chat.id
    
    # Get or create conversation history (which selects a product)
    conv_history = get_or_create_conversation_history(chat_id)
    product = conv_history['product']
    
    # Generate initial customer greeting using LLM
    try:
        initial_prompt = f"You are a customer who just entered a store. You are interested in buying {product}. Generate a natural, casual greeting message to start the conversation with the salesperson. Keep it brief (1-2 sentences) and friendly. Just write the greeting, nothing else."
        
        response = client.chat.completions.create(
            model="ft:gpt-3.5-turbo-0125:personal:your-fine-tuned-model-name:Cvi4Yd6v",
            messages=[
                {"role": "system", "content": "You are a customer shopping at a store. Generate natural, varied greeting messages."},
                {"role": "user", "content": initial_prompt}
            ],
            temperature=0.9,
            max_tokens=80
        )
        
        initial_message = response.choices[0].message.content.strip()
        print(f"[INFO] LLM-generated initial message: {initial_message}")
        
    except Exception as e:
        print(f"[ERROR] Failed to generate LLM greeting: {e}")
        # Fallback to static message
        initial_message = f"Hi! I'm interested in buying {product}. Can you help me find the right one?"
        print(f"[INFO] Using fallback message: {initial_message}")
        
    await update.message.reply_text(initial_message)
    
    # Add initial message to conversation history
    conv_history['messages'].append({
        "role": "assistant",
        "content": initial_message
    })
    
    # Log the message into the database
    insert_message(
        conversation_id=CONVERSATION_ID,
        role="customer",
        text=initial_message,
        chat_id=chat_id
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages"""
    user_message = update.message.text
    chat_id = update.message.chat.id
    username = update.message.from_user.username if update.message.from_user.username else "unknown"
    
    # Determine role based on username
    if username == VA_bot.lstrip('@'):
        bot_role = "salesperson"
        print(f"[SALESPERSON] {user_message}")
    else:
        bot_role = "customer"
        print(f"[CUSTOMER] {user_message}")
    
    # Insert incoming message into database
    insert_message(
        conversation_id=CONVERSATION_ID,
        role=bot_role,
        text=user_message,
        chat_id=chat_id
    )
    
    # Only generate response if the message is from salesperson
    if bot_role == "salesperson":
        # Get the AI customer response
        response = await gpt_customer_response(user_message, chat_id)
        
        print(f"[CUSTOMER-AI] {response}")
        
        # Insert customer response into database
        insert_message(
            conversation_id=CONVERSATION_ID,
            role="customer",
            text=response,
            chat_id=chat_id
        )
        
        # Send the response back to the Telegram user
        await update.message.reply_text(response)

async def gpt_customer_response(salesperson_message, chat_id):
    """Generate customer response using GPT with conversation memory"""
    
    # Get conversation history for this chat
    conv_history = get_or_create_conversation_history(chat_id)
    
    # Add salesperson's message to conversation history
    conv_history['messages'].append({
        "role": "user",
        "content": salesperson_message
    })
    
    try:
        # Call OpenAI API with full conversation history (NEW SYNTAX)
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
            
            # Regenerate response
            response = client.chat.completions.create(
                model="ft:gpt-3.5-turbo-0125:personal:your-fine-tuned-model-name:Cvi4Yd6v",
                messages=conv_history['messages'],
                temperature=0.7,
                max_tokens=150,
                top_p=0.92,
                frequency_penalty=0.5,
                presence_penalty=0.5,
                stop=["Salesperson:", "Sales person:", "Agent:", "SALESPERSON:"]
            )
            
            customer_response = response.choices[0].message.content.strip()
        
        # Add customer's response to conversation history
        conv_history['messages'].append({
            "role": "assistant",
            "content": customer_response
        })
        
        return customer_response
        
    except Exception as e:
        print(f"[ERROR] Error generating response: {str(e)}")
        return f"Sorry, something went wrong. Error: {str(e)}"  # Updated error message with more info

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset conversation for this chat and start fresh with new product"""
    chat_id = update.message.chat.id
    
    if chat_id in conversation_histories:
        old_product = conversation_histories[chat_id]['product']
        del conversation_histories[chat_id]
        print(f"[INFO] Conversation reset for chat {chat_id} (was: {old_product})")
        
        # Get new conversation with different product
        conv_history = get_or_create_conversation_history(chat_id)
        new_product = conv_history['product']
        
        # Generate new initial message with LLM
        try:
            initial_prompt = f"You are a customer who just entered a store. You are interested in buying {new_product}. Generate a natural, casual greeting message to start the conversation with the salesperson. Keep it brief (1-2 sentences) and friendly. Just write the greeting, nothing else."
            
            response = client.chat.completions.create(
               # model="gpt-3.5-turbo",
                model="ft:gpt-3.5-turbo-0125:personal:your-fine-tuned-model-name:Cvi4Yd6v",
                messages=[
                    {"role": "system", "content": "You are a customer shopping at a store. Generate natural, varied greeting messages."},
                    {"role": "user", "content": initial_prompt}
                ],
                temperature=0.9,
                max_tokens=80
            )
            
            initial_message = response.choices[0].message.content.strip()
            print(f"[INFO] New conversation started with: {new_product}")
            print(f"[INFO] LLM-generated message: {initial_message}")

        except Exception as e:
            print(f"[ERROR] Failed to generate LLM greeting: {e}")
            initial_message = f"Hi! I'm looking for {new_product}. Can you help me?"

        # Add initial message to conversation history
        conv_history['messages'].append({
            "role": "assistant",
            "content": initial_message
        })
        
        # Send the new greeting
        await update.message.reply_text(f"🔄 Conversation reset!\n\n{initial_message}")

        # Log the new message
        insert_message(
            conversation_id=CONVERSATION_ID,
            role="customer",
            text=initial_message,
            chat_id=chat_id
        )
    else:
        await update.message.reply_text("No active conversation to reset. Use /start to begin a new conversation!")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current conversation status and statistics"""
    chat_id = update.message.chat.id

    if chat_id in conversation_histories:
        conv_history = conversation_histories[chat_id]
        product = conv_history['product']

        # Count messages by role (excluding system messages)
        customer_messages = len([m for m in conv_history['messages'] if m['role'] == 'assistant'])
        salesperson_messages = len([m for m in conv_history['messages'] if m['role'] == 'user'])
        total_messages = customer_messages + salesperson_messages

        created_at = conv_history['created_at']
        created_datetime = datetime.fromisoformat(created_at)
        time_elapsed = datetime.now() - created_datetime

        # Format elapsed time
        minutes = int(time_elapsed.total_seconds() / 60)
        seconds = int(time_elapsed.total_seconds() % 60)
        
        if minutes > 0:
            time_str = f"{minutes}m {seconds}s"
        else:
            time_str = f"{seconds}s"

        status_message = f"""📊 Conversation Status:

🛍️ Current Product: {product}

💬 Message Count:
   • Customer (AI): {customer_messages}
   • Salesperson: {salesperson_messages}
   • Total: {total_messages}

⏱️ Duration: {time_str}

📅 Started: {created_datetime.strftime('%I:%M %p, %b %d')}

━━━━━━━━━━━━━━━━━━━━
💡 Use /reset to start fresh with a new product!
"""
        await update.message.reply_text(status_message)
    else:
        await update.message.reply_text("❌ No active conversation found.\n\n💡 Use /start to begin a new conversation!")

def main():
    """Initialize and run the bot"""
    if not TELEGRAM_BOT_TOKEN:
        print("[ERROR] TELEGRAM_BOT_1_TOKEN not found in environment variables!")
        return

    if not OPENAI_API_KEY:
        print("[ERROR] aluraagency_OPEPNAI_API_KEY not found in environment variables!")
        return
    
    _bot_application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add command handlers
    _bot_application.add_handler(CommandHandler('start', start))
    _bot_application.add_handler(CommandHandler('reset', reset))
    _bot_application.add_handler(CommandHandler('status', status))
    
    # Add message handler
    _bot_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("="*70)
    print("CUSTOMER BOT IS RUNNING".center(70))
    print("="*70)
    print("Features:")
    print("  ✓ Acts as a REAL CUSTOMER (never as salesperson)")
    print("  ✓ Varied product interests per conversation")
    print("  ✓ Conversation memory per chat")
    print("  ✓ OpenAI 1.x API integration")
    print("="*70)
    print("\nCommands:")
    print("  /start  - Start a new conversation")
    print("  /reset  - Reset current conversation")
    print("  /status - Show conversation status")
    print("="*70)
    print("\nWaiting for messages...\n")
    
    _bot_application.run_polling(drop_pending_updates=True, poll_interval=1)

if __name__ == '__main__':
    main()