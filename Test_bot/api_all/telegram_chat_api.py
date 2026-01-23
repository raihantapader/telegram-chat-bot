# telegram_chat_api.py
# API for Telegram Chat with person_id support

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
import uvicorn

load_dotenv()

# MongoDB connection
MongoDB_Url = os.getenv("DB_URI")
client = MongoClient(MongoDB_Url)
db = client['Raihan']
chat_collection = db['telegram_chats']
friends_collection = db['telegram_friends']

app = FastAPI(title="Telegram Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic model for performance update
class PerformanceUpdate(BaseModel):
    performance: str


def format_duration(seconds: float) -> str:
    """Format seconds into readable duration like '1 min 56 sec' or '2 hr 30 min'"""
    if seconds is None:
        return "N/A"
    
    seconds = int(seconds)
    
    if seconds < 60:
        return f"{seconds} sec"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        if secs > 0:
            return f"{minutes} min {secs} sec"
        return f"{minutes} min"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if minutes > 0:
            return f"{hours} hr {minutes} min"
        return f"{hours} hr"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        if hours > 0:
            return f"{days} day {hours} hr"
        return f"{days} day"


def calculate_avg_response_time(messages: list) -> Optional[float]:
    """Calculate average response time in seconds"""
    if len(messages) < 2:
        return None
    
    response_times = []
    
    for i in range(1, len(messages)):
        prev_msg = messages[i - 1]
        curr_msg = messages[i]
        
        # Only calculate when receiver replies to sender (or vice versa)
        if prev_msg.get("role") != curr_msg.get("role"):
            prev_time = prev_msg.get("timestamp")
            curr_time = curr_msg.get("timestamp")
            
            if prev_time and curr_time:
                diff = (curr_time - prev_time).total_seconds()
                # Only count reasonable response times (less than 24 hours)
                if 0 < diff < 86400:
                    response_times.append(diff)
    
    if response_times:
        return sum(response_times) / len(response_times)
    return None


@app.get("/")
def root():
    return {
        "message": "Telegram Chat API",
        "endpoints": {
            "GET /api/friends": "Get all friends list with start/end time",
            "GET /api/conversations": "Get all conversations together",
            "GET /api/messages/{person_id}": "Get stats + messages by person_id",
            "GET /api/stats/{person_id}": "Get statistics for specific person",
            "POST /api/performance/{person_id}": "Update performance for a person"
        }
    }


@app.get("/api/friends")
def get_all_friends():
    """Get all friends list with start_time and end_time"""
    try:
        friends = list(friends_collection.find({}).sort("person_id", 1))
        
        result = []
        for friend in friends:
            person_id = friend.get("person_id")
            
            # Get messages for this friend to find start/end time
            messages = list(chat_collection.find(
                {"person_id": person_id}
            ).sort("timestamp", 1))
            
            msg_count = len(messages)
            
            # Get first and last message timestamps
            start_time = None
            end_time = None
            if messages:
                start_time = messages[0].get("timestamp")
                end_time = messages[-1].get("timestamp")
            
            result.append({
                "person_id": person_id,
                "username": friend.get("username"),
                "name": friend.get("name"),
                "chat_id": friend.get("chat_id"),
                "total_messages": msg_count,
                "start_time": start_time,
                "end_time": end_time
            })
        
        return {
            "total_friends": len(result),
            "friends": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@app.get("/api/conversations")
def get_all_conversations():
    """Get all conversations together sorted by timestamp"""
    try:
        # Get all messages sorted by timestamp
        messages = list(chat_collection.find({}).sort("timestamp", 1))
        
        if not messages:
            return {
                "total_messages": 0,
                "conversations": []
            }
        
        # Format messages
        result = []
        for msg in messages:
            result.append({
                "person_id": msg.get("person_id"),
                "role": msg.get("role"),
                "name": msg.get("name"),
                "text": msg.get("text"),
                "timestamp": msg.get("timestamp")
            })
        
        return {
            "total_messages": len(result),
            "conversations": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@app.get("/api/messages/{person_id}")
def get_messages_by_person_id(person_id: int):
    """Get stats + messages by person_id"""
    try:
        # Get friend info
        friend = friends_collection.find_one({"person_id": person_id})
        
        if not friend:
            raise HTTPException(status_code=404, detail=f"Person {person_id} not found")
        
        # Get all messages for this person
        messages = list(chat_collection.find(
            {"person_id": person_id}
        ).sort("timestamp", 1))
        
        # Calculate statistics
        total = len(messages)
        sender_count = sum(1 for m in messages if m.get("role") == "sender")
        receiver_count = sum(1 for m in messages if m.get("role") == "receiver")
        
        # Duration
        first_message_at = None
        last_message_at = None
        duration_seconds = None
        
        if messages:
            first_message_at = messages[0].get("timestamp")
            last_message_at = messages[-1].get("timestamp")
            if first_message_at and last_message_at:
                duration_seconds = (last_message_at - first_message_at).total_seconds()
        
        # Average response time
        avg_response_seconds = calculate_avg_response_time(messages)
        
        # Get performance from friend document
        performance = friend.get("performance", None)
        
        # Format messages
        result_messages = []
        for msg in messages:
            result_messages.append({
                "message_id": msg.get("message_id"),
                "role": msg.get("role"),
                "name": msg.get("name"),
                "text": msg.get("text"),
                "timestamp": msg.get("timestamp")
            })
        
        return {
            "person_id": person_id,
            "friend_name": friend.get("name"),
            "friend_username": friend.get("username"),
            "chat_id": friend.get("chat_id"),
            "total_conversation": total,
            "total_sender_message": sender_count,
            "total_receiver_message": receiver_count,
            "duration": format_duration(duration_seconds),
            "avg_response_time": format_duration(avg_response_seconds),
            "performance": performance,
            "first_message_at": first_message_at,
            "last_message_at": last_message_at,
            "messages": result_messages
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@app.get("/api/stats/{person_id}")
def get_stats_by_person(person_id: int):
    """Get statistics for a specific person"""
    try:
        # Get friend info
        friend = friends_collection.find_one({"person_id": person_id})
        
        if not friend:
            raise HTTPException(status_code=404, detail=f"Person {person_id} not found")
        
        # Get messages
        messages = list(chat_collection.find(
            {"person_id": person_id}
        ).sort("timestamp", 1))
        
        total = len(messages)
        sender_count = sum(1 for m in messages if m.get("role") == "sender")
        receiver_count = sum(1 for m in messages if m.get("role") == "receiver")
        
        # Duration
        first_message_at = None
        last_message_at = None
        duration_seconds = None
        
        if messages:
            first_message_at = messages[0].get("timestamp")
            last_message_at = messages[-1].get("timestamp")
            if first_message_at and last_message_at:
                duration_seconds = (last_message_at - first_message_at).total_seconds()
        
        # Average response time
        avg_response_seconds = calculate_avg_response_time(messages)
        
        # Get performance
        performance = friend.get("performance", None)
        
        return {
            "person_id": person_id,
            "friend_name": friend.get("name"),
            "friend_username": friend.get("username"),
            "chat_id": friend.get("chat_id"),
            "total_conversation": total,
            "total_sender_message": sender_count,
            "total_receiver_message": receiver_count,
            "duration": format_duration(duration_seconds),
            "avg_response_time": format_duration(avg_response_seconds),
            "performance": performance,
            "first_message_at": first_message_at,
            "last_message_at": last_message_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@app.post("/api/performance/{person_id}")
def update_performance(person_id: int, data: PerformanceUpdate):
    """Update performance for a specific person"""
    try:
        # Check if person exists
        friend = friends_collection.find_one({"person_id": person_id})
        
        if not friend:
            raise HTTPException(status_code=404, detail=f"Person {person_id} not found")
        
        # Update performance field
        result = friends_collection.update_one(
            {"person_id": person_id},
            {"$set": {"performance": data.performance, "performance_updated_at": datetime.now()}}
        )
        
        if result.modified_count > 0:
            return {
                "message": f"Performance updated for Person {person_id}",
                "person_id": person_id,
                "performance": data.performance
            }
        else:
            return {
                "message": "No changes made",
                "person_id": person_id,
                "performance": data.performance
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@app.delete("/api/messages/{person_id}")
def delete_messages_by_person(person_id: int):
    """Delete all messages for a specific person"""
    try:
        friend = friends_collection.find_one({"person_id": person_id})
        
        if not friend:
            raise HTTPException(status_code=404, detail=f"Person {person_id} not found")
        
        result = chat_collection.delete_many({"person_id": person_id})
        
        return {
            "message": f"Deleted {result.deleted_count} messages for Person {person_id}",
            "deleted_count": result.deleted_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("TELEGRAM CHAT API".center(60))
    print("=" * 60)
    print("\nEndpoints:")
    print("  GET    /api/friends               - All friends with start/end time")
    print("  GET    /api/conversations         - All conversations together")
    print("  GET    /api/messages/{person_id}  - Stats + messages")
    print("  GET    /api/stats/{person_id}     - Only statistics")
    print("  POST   /api/performance/{person_id} - Update performance")
    print("  DELETE /api/messages/{person_id}  - Delete person's messages")
    print("=" * 60)
    print("\nServer: http://10.10.20.111:8090")
    print("Docs:   http://10.10.20.111:8090/docs")
    print("=" * 60 + "\n")
    
    uvicorn.run(app, host="10.10.20.111", port=8090, reload=True)