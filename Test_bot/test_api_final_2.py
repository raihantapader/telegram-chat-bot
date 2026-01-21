import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

load_dotenv()

MongoDB_Url = os.getenv("MONGODB_URI")
client = MongoClient(MongoDB_Url)
db = client['Raihan']
collection = db['chat_bot']
scores_collection = db['evaluation_scores']
test_collection = db['active_test_ids']

SALES_PERSON_USERNAME = os.getenv("SALES_PERSON_USERNAME", "raihantapader")


def get_latest_test_id():
    """Get the most recent active test_id from database"""
    try:
        latest_test = test_collection.find_one(
            {"status": "active"},
            sort=[("created_at", -1)]
        )
        if latest_test:
            return latest_test['test_id']
        return "default"
    except Exception as e:
        print(f"[DB] Error: {e}")
        return "default"


# FastAPI app
app = FastAPI(
    title="Conversation Management API",
    description="API for storing and retrieving Telegram conversations",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic Models
class MessageOutput(BaseModel):
    bot_name: str
    role: str
    text: str
    time: datetime


class ConversationStats(BaseModel):
    test_id: str
    total_messages: int
    customer_messages: int
    salesperson_messages: int
    duration: Optional[str]
    score: str
    english_level: str
    level_description: str
    response_time: str
    start_time: Optional[datetime]
    end_time: Optional[datetime]


# API Endpoints

@app.get("/")
def root():
    """Root endpoint - API information"""
    return {
        "message": "Conversation Management API",
        "description": "API for storing and retrieving Telegram conversations",
        "endpoints": {
            "GET /api/latest_test_id": "Get the latest active test_id",
            "GET /api/room_id/{room_id}/{conversation_id}": "Get all messages for a room and conversation",
            "GET /api/conversations": "Get all conversations with evaluation scores",
            "GET /api/stats/{test_id}": "Get conversation statistics"
        }
    }


@app.get("/api/latest_test_id")
def get_current_test_id():
    """Get the latest active test_id from database"""
    test_id = get_latest_test_id()
    return {
        "test_id": test_id,
        "status": "active" if test_id != "default" else "no_active_test"
    }


@app.get("/api/{room_id}/{conversation_id}", response_model=List[MessageOutput])
def get_room_conversation(room_id: int, conversation_id: str):
    """
    GET method to fetch all messages for a specific room_id and conversation_id, sorted by timestamp.
    """
    try:
        messages_cursor = collection.find({
            "room_id": room_id,
            "conversation_id": conversation_id
        }).sort("timestamp", 1)
        
        messages_list = list(messages_cursor)
        
        if not messages_list:
            raise HTTPException(
                status_code=404,
                detail=f"No messages found for room_id: {room_id}, conversation_id: {conversation_id}"
            )
        
        formatted_messages = []
        for msg in messages_list:
            formatted_messages.append({
                "bot_name": msg.get("bot", "Unknown"),
                "role": msg.get("role", "Unknown"),
                "text": msg.get("text", ""),
                "time": msg.get("timestamp")
            })
        
        return formatted_messages
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@app.get("/api/conversations")
def get_all_conversations():
    """
    GET method to fetch all conversations with evaluation scores.
    """
    try:
        evaluated_tests = list(scores_collection.find({}))
        
        if not evaluated_tests:
            return {"total_conversations": 0, "conversations": []}
        
        conversations = []
        
        for eval_record in evaluated_tests:
            test_id = eval_record.get("test_id")
            if not test_id:
                continue
            
            message_count = collection.count_documents({"conversation_id": test_id})
            if message_count == 0:
                continue
            
            total_messages = message_count
            customer_messages = collection.count_documents({"conversation_id": test_id, "role": "customer"})
            salesperson_messages = collection.count_documents({"conversation_id": test_id, "role": "salesperson"})
            
            first_msg = collection.find_one({"conversation_id": test_id}, sort=[("timestamp", 1)])
            last_msg = collection.find_one({"conversation_id": test_id}, sort=[("timestamp", -1)])
            
            duration_str = "N/A"
            if first_msg and last_msg:
                duration = last_msg["timestamp"] - first_msg["timestamp"]
                total_seconds = int(duration.total_seconds())
                hours = total_seconds // 3600
                total_seconds %= 3600
                minutes = total_seconds // 60
                seconds = total_seconds % 60
                duration_str = f"{hours} Hr {minutes} Min {seconds} Sec"
            
            avg_response_time = calculate_average_response_time(test_id)
            
            conversations.append({
                "test_id": test_id,
                "response_time": avg_response_time,
                "score": eval_record.get("score", "N/A"),
                "english_level": eval_record.get("english_level", "N/A"),
                "level_description": eval_record.get("assessment", "N/A"),
                "total_messages": total_messages,
                "customer_messages": customer_messages,
                "salesperson_messages": salesperson_messages,
                "test_duration": duration_str,
                "start_time": first_msg["timestamp"] if first_msg else None,
                "end_time": last_msg["timestamp"] if last_msg else None
            })
        
        return {"total_conversations": len(conversations), "conversations": conversations}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


def calculate_average_response_time(conversation_id: str):
    """Calculate average response time between customer and salesperson messages"""
    try:
        all_messages = list(collection.find(
            {"conversation_id": conversation_id}
        ).sort("timestamp", 1))
        
        if len(all_messages) < 2:
            return "N/A"
        
        response_times = []
        
        for i in range(len(all_messages) - 1):
            current_msg = all_messages[i]
            next_msg = all_messages[i + 1]
            
            if current_msg.get("role") != next_msg.get("role"):
                time_diff = next_msg["timestamp"] - current_msg["timestamp"]
                response_time_seconds = time_diff.total_seconds()
                if response_time_seconds > 0:
                    response_times.append(response_time_seconds)
        
        if not response_times:
            return "N/A"
        
        avg_response_time = sum(response_times) / len(response_times)
        
        if avg_response_time < 60:
            return f"{avg_response_time:.1f} sec"
        elif avg_response_time < 3600:
            return f"{avg_response_time / 60:.1f} min"
        else:
            return f"{avg_response_time / 3600:.1f} hr"
            
    except Exception as e:
        print(f"[ERROR] {e}")
        return "N/A"


@app.get("/api/stats/{test_id}", response_model=ConversationStats)
def get_conversation_stats(test_id: str):
    """
    GET method to fetch statistics for a specific test_id.
    """
    try:
        total_messages = collection.count_documents({"conversation_id": test_id})
        
        if total_messages == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No messages found for test_id: {test_id}"
            )
        
        customer_messages = collection.count_documents({
            "conversation_id": test_id,
            "role": "customer"
        })
        
        salesperson_messages = collection.count_documents({
            "conversation_id": test_id,
            "role": "salesperson"
        })
        
        first_msg = collection.find_one(
            {"conversation_id": test_id},
            sort=[("timestamp", 1)]
        )
        last_msg = collection.find_one(
            {"conversation_id": test_id},
            sort=[("timestamp", -1)]
        )
        
        duration_str = None
        if first_msg and last_msg:
            duration = last_msg["timestamp"] - first_msg["timestamp"]
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            total_seconds %= 3600
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            duration_str = f"{hours} Hr {minutes} Min {seconds} Sec"
        
        result_data = scores_collection.find_one({"test_id": test_id})
        
        score = "N/A"
        english_level = "N/A"
        level_description = "N/A"
        
        if result_data:
            score = result_data.get("score", "N/A")
            english_level = result_data.get("english_level", "N/A")
            level_description = result_data.get("assessment", "N/A")
        
        response_time = calculate_average_response_time(test_id)
        
        return {
            "test_id": test_id,
            "total_messages": total_messages,
            "customer_messages": customer_messages,
            "salesperson_messages": salesperson_messages,
            "duration": duration_str,
            "score": score,
            "english_level": english_level,
            "level_description": level_description,
            "response_time": response_time,
            "start_time": first_msg["timestamp"] if first_msg else None,
            "end_time": last_msg["timestamp"] if last_msg else None,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


if __name__ == "__main__":
    print("="*70)
    print("CONVERSATION MANAGEMENT API SERVER".center(70))
    print("="*70)
    print("\nAPI Endpoints:")
    print("  GET  /                                        - Root")
    print("  GET  /api/latest_test_id                      - Get current active test_id")
    print("  GET  /api/room_id/{room_id}/{conversation_id} - Get room conversation")
    print("  GET  /api/conversations                       - Get all conversations")
    print("  GET  /api/stats/{test_id}                     - Get conversation stats")
    print("="*70)
    print("\nServer running at: http://10.10.20.111:8086")
    print("API Documentation: http://10.10.20.111:8086/docs")
    print("="*70 + "\n")

    uvicorn.run(app, host="10.10.20.111", port=8086, reload=True)