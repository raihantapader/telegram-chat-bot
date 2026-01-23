import os
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

MongoDB_Url = os.getenv("MONGODB_URI")
client = MongoClient(MongoDB_Url)
db = client['Raihan']
chat_collection = db['chat_bot']
test_collection = db['active_test_ids']


def insert_message(conversation_id: str, role: str, text: str, chat_id: int, bot_name: str = "unknown"):
    """Insert a message into the database"""
    
    test_id = get_latest_test_id()  # Always use the latest test_id
    
    message = {
        "conversation_id": test_id,
        "bot": bot_name,
        "role": role,
        "text": text,
        "chat_id": chat_id,
        "timestamp": datetime.utcnow()
    }
    
    # Insert the message into the database
    result = chat_collection.insert_one(message)
    print(f"[DB] Saved {role} message (ID: {result.inserted_id})")
    return result.inserted_id



def get_latest_test_id():
    """Get the most recent active test_id"""
    try:
        # Fetch the most recent test_id where status is active
        latest_test = test_collection.find_one(
            {"status": "active"},
            sort=[("created_at", -1)]  # Sort by creation date to get the latest one
        )
        
        if latest_test:
            return latest_test['test_id']
        else:
            print("⚠️  No active test_id found in database. Using default.")
            return "default"
    except Exception as e:
        print(f"[DB] Error: {e}")
        return "default"


def get_conversation_by_test_id(test_id: str):
    """Retrieve conversation history by test_id"""
    try:
        messages_cursor = chat_collection.find(
            {"conversation_id": test_id}
        ).sort("timestamp", 1)
        
        messages_list = list(messages_cursor)
        
        if not messages_list:
            print(f"[DB] No messages found for test_id: {test_id}")
            return []
        
        print(f"[DB] Retrieved {len(messages_list)} messages for test_id: {test_id}")
        return messages_list

    except Exception as e:
        print(f"[DB] Error: {e}")
        return []


def get_all_test_ids():
    """Fetch all test_ids"""
    try:
        test_ids = test_collection.find({}).sort("created_at", -1)
        return list(test_ids)
    except Exception as e:
        print(f"[DB] Error: {e}")
        return []