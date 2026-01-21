import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
from pydantic import BaseModel, Field
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


# Helper function to get latest test_id
def get_latest_test_id():
    """Get the most recent active test_id from database"""
    try:
        latest_test = test_collection.find_one(
            {"status": "active"},
            sort=[("created_at", -1)]
        )
        
        if latest_test:
            return latest_test['test_id']
        else:
            print("⚠️  No active test_id found in database. Using default.")
            return "default"
    except Exception as e:
        print(f"[DB] Error: {e}")
        return "default"


# FastAPI app
app = FastAPI(
    title="Conversation Management API",
    description="API for storing and retrieving Telegram conversations",
)

# Add CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models for output messages
class MessageOutput(BaseModel):
    """Model for outgoing GET responses"""
    conversation_id: str
    bot: str
    role: str
    message: str
    timestamp: datetime

# Pydantic Models for conversation list item
class ConversationItem(BaseModel):
    """Model for individual conversation in the list"""
    test_id: str
    response_time: str
    score: str
    english_level: str
    level_description: str
    total_messages: int
    customer_messages: int
    salesperson_messages: int
    test_duration: str
    start_time: Optional[datetime]
    end_time: Optional[datetime]

# Pydantic Models for conversation statistics
class ConversationStats(BaseModel):
    """Model for conversation statistics"""
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

# First API endpoint to check server status
@app.get("/")
def root():
    """Root endpoint - API information"""
    return {
        "message": "Conversation Management API",
        "description": "API for storing and retrieving Telegram conversations",
        "endpoints": {
            "GET /api/latest_test_id": "Get the latest active test_id",
            "GET /api/dashboard/{conversation_id}": "Get all messages for a conversation ID",
            "GET /api/conversations": "Get list of all conversations with evaluation scores",
            "GET /api/stats/{conversation_id}": "Get conversation statistics"
        }
    }

# New endpoint to get latest test_id
@app.get("/api/latest_test_id")
def get_current_test_id():
    """Get the latest active test_id from database"""
    test_id = get_latest_test_id()
    return {
        "test_id": test_id,
        "status": "active" if test_id != "default" else "no_active_test"
    }

# Second API endpoint to get conversation by ID
@app.get("/api/dashboard/{conversation_id}", response_model=List[MessageOutput])
def get_conversation(conversation_id: str):
    """
    GET method to fetch all messages for a specific conversation ID, sorted by timestamp.
    """
    try:
        # Find all messages for this conversation and sort by timestamp
        messages_cursor = collection.find(
            {"conversation_id": conversation_id}
        ).sort("timestamp", 1)  # 1 = ascending order (oldest first)
        
        # Convert to list
        messages_list = list(messages_cursor)
        
        if not messages_list:
            raise HTTPException(
                status_code=404, 
                detail=f"No messages found for conversation_id: {conversation_id}"
            )
        
        # Transform to match output format
        formatted_messages = []
        for msg in messages_list:
            formatted_messages.append({
                "conversation_id": msg["conversation_id"],
                "bot": msg["bot"],  # This will be customer_1, customer_2, etc. or salesperson username
                "role": msg["role"],  # customer or salesperson
                "message": msg["text"],  # Rename 'text' to 'message'
                "timestamp": msg["timestamp"]
            })
        
        return formatted_messages
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving messages: {str(e)}")

def calculate_average_response_time(conversation_id: str):
    """Calculate average response time between customer and salesperson messages"""
    try:
        # Get all messages sorted by timestamp
        all_messages = list(collection.find(
            {"conversation_id": conversation_id}
        ).sort("timestamp", 1))
        
        if len(all_messages) < 2:
            return "N/A"
        
        response_times = []
        
        # Iterate through consecutive messages
        for i in range(len(all_messages) - 1):
            current_msg = all_messages[i]
            next_msg = all_messages[i + 1]
            
            current_role = current_msg.get("role")
            next_role = next_msg.get("role")
            
            # Only calculate if roles are different (one person responds to another)
            if current_role != next_role:
                time_diff = next_msg["timestamp"] - current_msg["timestamp"]
                response_time_seconds = time_diff.total_seconds()
                
                # Only count positive response times
                if response_time_seconds > 0:
                    response_times.append(response_time_seconds)
        
        if not response_times:
            return "N/A"
        
        # Calculate average
        avg_response_time = sum(response_times) / len(response_times)
        
        # Format output
        if avg_response_time < 60:
            return f"{avg_response_time:.1f} sec"
        elif avg_response_time < 3600:
            minutes = avg_response_time / 60
            return f"{minutes:.1f} min"
        else:
            hours = avg_response_time / 3600
            return f"{hours:.1f} hr"
            
    except Exception as e:
        print(f"[ERROR] Failed to calculate response time for {conversation_id}: {e}")
        return "N/A"

# Third API endpoint to get all conversation IDs with evaluation
@app.get("/api/conversations")
def get_all_conversations():
    """
    GET method to fetch all unique conversation IDs with evaluation scores.
    Only shows conversations that have evaluation scores.
    """
    try:
        # Get all test_ids that have evaluation scores
        evaluated_tests = list(scores_collection.find({}))
        
        if not evaluated_tests:
            return {
                "total_conversations": 0,
                "conversations": []
            }
        
        conversations = []
        
        for eval_record in evaluated_tests:
            test_id = eval_record.get("test_id")
            
            if not test_id:
                continue
                
            print(f"\n[INFO] Processing test_id: {test_id}")
            
            # Check if this test_id has messages in chat_bot collection
            message_count = collection.count_documents({"conversation_id": test_id})
            
            if message_count == 0:
                print(f"[WARNING] No messages found for test_id: {test_id}")
                continue
            
            # Count total messages
            total_messages = collection.count_documents({"conversation_id": test_id})
            
            # Count by role
            customer_messages = collection.count_documents({
                "conversation_id": test_id,
                "role": "customer"
            })
            salesperson_messages = collection.count_documents({
                "conversation_id": test_id,
                "role": "salesperson"
            })
            
            # Get first and last message
            first_msg = collection.find_one(
                {"conversation_id": test_id},
                sort=[("timestamp", 1)]
            )
            last_msg = collection.find_one(
                {"conversation_id": test_id},
                sort=[("timestamp", -1)]
            )
            
            # Calculate test duration
            duration_str = "N/A"
            if first_msg and last_msg:
                duration = last_msg["timestamp"] - first_msg["timestamp"]
                total_seconds = int(duration.total_seconds())
     
                hours = total_seconds // 3600
                total_seconds %= 3600
                minutes = total_seconds // 60
                seconds = total_seconds % 60

                duration_str = f"{hours} Hr {minutes} Min {seconds} Sec"
            
            # Calculate average response time
            avg_response_time = calculate_average_response_time(test_id)
            print(f"[INFO] Average response time: {avg_response_time}")
            
            # Get evaluation data (already have it from eval_record)
            score = eval_record.get("score", "N/A")
            english_level = eval_record.get("english_level", "N/A")
            level_description = eval_record.get("assessment", "N/A")
            
            print(f"[SUCCESS] Evaluation: Score={score}, Level={english_level}")
            
            # Build conversation object
            conversations.append({
                "test_id": test_id,
                "response_time": avg_response_time,
                "score": score,
                "english_level": english_level,
                "level_description": level_description,
                "total_messages": total_messages,
                "customer_messages": customer_messages,
                "salesperson_messages": salesperson_messages,
                "test_duration": duration_str,
                "start_time": first_msg["timestamp"] if first_msg else None,
                "end_time": last_msg["timestamp"] if last_msg else None
            })
        
        print(f"\n[INFO] Successfully processed {len(conversations)} conversations")
        
        return {
            "total_conversations": len(conversations),
            "conversations": conversations
        }
        
    except Exception as e:
        print(f"[ERROR] Error in get_all_conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving conversations: {str(e)}")

# Fourth API endpoint to get conversation statistics
@app.get("/api/stats/{test_id}", response_model=ConversationStats)
def get_conversation_stats(test_id: str):
    """
    GET method to fetch statistics for a specific test_id.
    """
    try:
        # Count total messages
        total_messages = collection.count_documents({"conversation_id": test_id})
        
        if total_messages == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No messages found for test_id: {test_id}"
            )
        
        # Count by role
        customer_messages = collection.count_documents({
            "conversation_id": test_id,
            "role": "customer"
        })
        
        salesperson_messages = collection.count_documents({
            "conversation_id": test_id,
            "role": "salesperson"
        })
        
        # Get first and last message
        first_msg = collection.find_one(
            {"conversation_id": test_id},
            sort=[("timestamp", 1)]
        )
        last_msg = collection.find_one(
            {"conversation_id": test_id},
            sort=[("timestamp", -1)]
        )
        
        # Calculate duration
        duration_str = None
        if first_msg and last_msg:
            duration = last_msg["timestamp"] - first_msg["timestamp"]
            total_seconds = int(duration.total_seconds())
 
            hours = total_seconds // 3600
            total_seconds %= 3600
            minutes = total_seconds // 60
            seconds = total_seconds % 60

            duration_str = f"{hours} Hr {minutes} Min {seconds} Sec"
        
        # Get evaluation data from evaluation_scores collection
        result_data = scores_collection.find_one({"test_id": test_id})
        
        # Default values
        score = "N/A"
        english_level = "N/A"
        level_description = "N/A"
        
        # Extract evaluation results
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
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")

# Run the server
if __name__ == "__main__":
    print("="*70)
    print("CONVERSATION MANAGEMENT API SERVER".center(70))
    print("="*70)
    print("\nAPI Endpoints:")
    print("  GET    /api/latest_test_id                - Get current active test_id")
    print("  GET    /api/dashboard/{test_id}           - Get conversation messages")
    print("  GET    /api/conversations                 - Get all conversations with scores")
    print("  GET    /api/stats/{test_id}               - Get conversation stats")
    print("="*70)
    print("\nServer running at: http://10.10.20.111:8089")
    print("API Documentation: http://10.10.20.111:8089/docs")
    print("="*70 + "\n")
    
    uvicorn.run(app, host="10.10.20.111", port=8089, reload=True)