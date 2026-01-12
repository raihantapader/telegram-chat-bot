import os
import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_1_TOKEN")
OPENAI_API_KEY = os.getenv("aluraagency_OPEPNAI_API_KEY")

# Configure OpenAI
openai.api_key = OPENAI_API_KEY

# Store active tests and conversation history
active_tests = {}
conversation_history = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command with test ID"""
    
    if context.args and len(context.args) > 0:
        test_id = context.args[0].upper()
        chat_id = update.message.chat.id
        
        # Store test ID
        active_tests[chat_id] = test_id
        
        # Initialize conversation history
        conversation_history[chat_id] = [
            {"role": "system", "content": "You are a customer interested in buying products. You are asking questions to a salesperson. Be curious and ask relevant questions about pricing, features, delivery, etc."}
        ]
        
        # Welcome message
        await update.message.reply_text(
            f"✅ Customer Bot Started\n\n"
            f"Test ID: {test_id}\n\n"
        )
        
        # Generate first customer message using GPT
        customer_message = await generate_customer_message(chat_id, "Hello, I'm interested in your products.")
        
        await update.message.reply_text(
            f"*Customer*: {customer_message}",
            parse_mode="Markdown"
        )
        
    else:
        await update.message.reply_text(
            "Please use: /start <TestID>\n"
            "Example: /start A423D6"
        )

async def generate_customer_message(chat_id, salesperson_reply=None):
    
    try:
        # Add salesperson's reply to history if provided
        if salesperson_reply:
            conversation_history[chat_id].append({
                "role": "user", 
                "content": salesperson_reply
            })
        
        # Generate customer response
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=conversation_history[chat_id],
            max_tokens=150,
            temperature=0.8
        )
        
        customer_message = response.choices[0].message.content
        
        # Add customer message to history
        conversation_history[chat_id].append({
            "role": "assistant",
            "content": customer_message
        })
        
        return customer_message
        
    except Exception as e:
        print(f"Error generating message: {e}")
        # Fallback responses
        fallback_responses = [
            "That sounds interesting! Can you tell me more?",
            "I have a question about pricing.",
            "What features does this product have?",
            "How soon can I get delivery?",
            "Do you offer any discounts?",
            "Can you send me more information?",
        ]
        import random
        return random.choice(fallback_responses)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle salesperson messages and generate customer replies"""
    
    chat_id = update.message.chat.id
    
    # Check if user has active test
    if chat_id not in active_tests:
        await update.message.reply_text(
            "Please start a test first with: /start <TestID>"
        )
        return
    
    # Get test ID
    test_id = active_tests[chat_id]
    
    # Get salesperson's message (your message)
    salesperson_message = update.message.text
    
    # Show salesperson message
    await update.message.reply_text(
        f"👤 *You (Salesperson)*: {salesperson_message}",
        parse_mode="Markdown"
    )
    
    # Generate and send customer response
    await update.message.reply_text("🤖 *Customer is typing...*", parse_mode="Markdown")
    
    customer_response = await generate_customer_message(chat_id, salesperson_message)
    
    await update.message.reply_text(
        f"*Customer*: {customer_response}",
        parse_mode="Markdown"
    )
    
    # Print log
    print(f"Test {test_id}: Salesperson replied, Customer responded")

async def end_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """End the current test"""
    
    chat_id = update.message.chat.id
    
    if chat_id in active_tests:
        test_id = active_tests[chat_id]
        
        # Count conversation turns
        if chat_id in conversation_history:
            turns = len([msg for msg in conversation_history[chat_id] if msg["role"] == "assistant"])
        else:
            turns = 0
        
        await update.message.reply_text(
            f"✅ Test Ended\n\n"
            f"Test ID: {test_id}\n"
            f"Conversation turns: {turns}\n\n"
        )
        
        # Clean up
        if chat_id in active_tests:
            del active_tests[chat_id]
        if chat_id in conversation_history:
            del conversation_history[chat_id]
    else:
        await update.message.reply_text("No active test to end.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help"""
    
    await update.message.reply_text(
        "*Customer Bot Help*\n\n"
        "/start <TestID> - Start test\n",
        parse_mode="Markdown"
    )

def main():
    """Start the bot"""
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("end", end_test))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print(" Customer Bot is running...")
    print(" Bot acts as CUSTOMER (AI), you act as SALESPERSON")
    app.run_polling()

if __name__ == "__main__":
    main()