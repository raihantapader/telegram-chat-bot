import os
from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
from pydantic import BaseModel
from typing import List

load_dotenv()

MongoDB_Url = os.getenv("MONGODB_URI")
client = MongoClient(MongoDB_Url)
db = client['Raihan']
collection = db['chat_bot']

SALES_PERSON_USERNAME = os.getenv("SALES_PERSON_USERNAME", "raihtapader")
CUSTOMER_BOT_USERNAME = os.getenv("CUSTOMER_BOT_USERNAME", "customerBot_1")

# FastAPI app
app = FastAPI()

class Message(BaseModel):
    conversation_id: str
    bot: str
    role: str
    text: str
    timestamp: datetime
   # chat_id: int

def insert_message(conversation_id: str, bot: str, role: str, text: str, timestamp: datetime):
    """
    Insert a message into the database.

    Args:
        conversation_id: The conversation ID
        bot: The bot username
        role: Either "salesperson" or "customer"
        text: The message text
        timestamp: The timestamp of the message
    """

    if role == "salesperson":
        bot_username = SALES_PERSON_USERNAME
    elif role == "customer":
        bot_username = CUSTOMER_BOT_USERNAME
    else:
        bot_username = "unknown"

    # Create the message document
    message = {
        "conversation_id": conversation_id,
        "bot": bot_username,
        "role": role,
        "text": text,
        #"chat_id": chat_id,
        "timestamp": datetime.now()
    }

    collection.insert_one(message)
    print(f"[DB] Saved {role} message to database")

#@app.post("/message")
#def post_message(message: Message):
    #"""
   # POST method to store a new message in the database.

    #Args:
       # message: Message data to be saved
    #"""
   # try:
       # insert_message(message.conversation_id, message.bot, message.role, message.text, message.timestamp)
       # return {"message": "Message saved successfully"}
    #except Exception as e:
       # raise HTTPException(status_code=500, detail=str(e))

@app.get("/messages/{conversation_id}", response_model=List[Message])
def get_messages(conversation_id: str):
    """
    GET method to fetch messages by conversation ID.

    Args:
        conversation_id: The ID of the conversation to retrieve messages for
    """
    messages_cursor = collection.find({"conversation_id": conversation_id})

    if not messages_cursor:
        raise HTTPException(status_code=404, detail="No messages found for this conversation.")

    # Convert MongoDB documents to Pydantic model instances
    messages = []
    for message in messages_cursor:
        message['_id'] = str(message['_id'])
        messages.append(message)

    return messages
