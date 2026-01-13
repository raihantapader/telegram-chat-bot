import os
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

MongoDB_Url = os.getenv("MONGODB_URI")  
client = MongoClient(MongoDB_Url)
db = client['Raihan']  # Database name
collection = db['chat_bot']  # collection name to store conversation

# Get the usernames from environment variables
SALES_PERSON_USERNAME = os.getenv("SALES_PERSON_USERNAME", "raihtapader")
CUSTOMER_BOT_USERNAME = os.getenv("CUSTOMER_BOT_USERNAME", "customerBot_1")


def insert_message(conversation_id: str, role: str, text: str, chat_id: int):
    """
    Insert a message into the database.
    
    Args:
        conversation_id: The conversation ID
        role: Either "salesperson" or "customer"
        text: The message text
        chat_id: The Telegram chat ID
    """
    
    if role == "salesperson":
        bot_username = SALES_PERSON_USERNAME  # If the role is salesperson, use your username
    elif role == "customer":
        bot_username = CUSTOMER_BOT_USERNAME
    else:
        bot_username = "unknown"
        
    # Create the message to insert into the database
    message = {
        "conversation_id": conversation_id,
        "bot": bot_username,
        "role": role,  
        "text": text,
        "chat_id": chat_id,
        "timestamp": datetime.now() 
    }
    
    collection.insert_one(message)
    print(f"[DB] Saved {role} message to database")