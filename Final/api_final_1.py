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

SALES_PERSON_USERNAME = os.getenv("SALES_PERSON_USERNAME", "raihantapader")
CUSTOMER_BOT_USERNAME = os.getenv("CUSTOMER_BOT_USERNAME", "customerBot_1")


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
    conversation_id: str
    bot_name: str
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
    conversation_id: str
    customer_name: str
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

# Helper function
def insert_message(conversation_id: str, role: str, text: str, chat_id: int):

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
        "chat_id": chat_id,
        "timestamp": datetime.utcnow()  # Use UTC time for consistency
    }
    
    result = collection.insert_one(message)
    print(f"[DB] Saved {role} message to database (ID: {result.inserted_id})")
    return result.inserted_id

# API Endpoints

# First API endpoint to check server status
@app.get("/")
def root():
    """Root endpoint - API information"""
    return {
        "message": "Conversation Management API",
        "description": "API for storing and retrieving Telegram conversations",
        "endpoints": {
            "GET /api/dashboard/{conversation_id}": "Get all messages for a conversation ID",
            "GET /api/conversations": "Get list of all conversations with evaluation scores",
            "GET /api/stats/{conversation_id}": "Get conversation statistics"
        }
    }

# Second API endpoint to get conversation by ID
@app.get("/api/dashboard/{conversation_id}", response_model=List[MessageOutput])
def get_conversation(conversation_id: str):
    
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
                "bot": msg["bot"],
                "role": msg["role"],
                "message": msg["text"],  # Rename 'text' to 'message'
                "timestamp": msg["timestamp"]
            })
        
        return formatted_messages
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving messages: {str(e)}")

def calculate_average_response_time(conversation_id: str):
    
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
                
                # Only count positive response times (shouldn't have negative, but just in case)
                if response_time_seconds > 0:
                    response_times.append(response_time_seconds)
        
        if not response_times:
            return "N/A"
        
        # Calculate average
        avg_response_time = sum(response_times) / len(response_times)
        
        # Format output
        if avg_response_time < 60:
            # Less than 1 minute - show in seconds
            return f"{avg_response_time:.1f} sec"
        elif avg_response_time < 3600:
            # Less than 1 hour - show in minutes
            minutes = avg_response_time / 60
            return f"{minutes:.1f} min"
        else:
            # Show in hours
            hours = avg_response_time / 3600
            return f"{hours:.1f} hr"
            
    except Exception as e:
        print(f"[ERROR] Failed to calculate response time for {conversation_id}: {e}")
        return "N/A"

# Third API endpoint to get all conversation IDs with evaluation
@app.get("/api/conversations")
def get_all_conversations():
    try:
        # Get distinct conversation IDs
        conversation_ids = collection.distinct("conversation_id")
        
        if not conversation_ids:
            return {
                "total_conversations": 0,
                "conversations": []
            }
        
        # Get message count and evaluation for each conversation
        conversations = []
        for conv_id in conversation_ids:
            print(f"\n[INFO] Processing conversation: {conv_id}")
            
            # Count total messages
            total_messages = collection.count_documents({"conversation_id": conv_id})
            
            # Count by role
            customer_messages = collection.count_documents({
                "conversation_id": conv_id,
                "role": "customer"
            })
            salesperson_messages = collection.count_documents({
                "conversation_id": conv_id,
                "role": "salesperson"
            })
            
            # Get first and last message (from ALL messages)
            first_msg = collection.find_one(
                {"conversation_id": conv_id},
                sort=[("timestamp", 1)]
            )
            last_msg = collection.find_one(
                {"conversation_id": conv_id},
                sort=[("timestamp", -1)]
            )
            
            # Calculate test duration (from first to last message of entire conversation)
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
            avg_response_time = calculate_average_response_time(conv_id)
            print(f"[INFO] Average response time: {avg_response_time}")
            
            # Get evaluation data from evaluation_scores collection
            result_data = scores_collection.find_one({"test_id": conv_id})
            
            # Default values in case evaluation not found
            score = "N/A"
            english_level = "N/A"
            level_description = "N/A"
            
            # Extract evaluation results if available
            if result_data:
                score = result_data.get("score", "N/A")
                english_level = result_data.get("english_level", "N/A")
                level_description = result_data.get("assessment", "N/A")
                print(f"[SUCCESS] Evaluation found: Score={score}, Level={english_level}")
            else:
                print(f"[WARNING] No evaluation data found for {conv_id}")
            
            # Build conversation object
            conversations.append({
                "conversation_id": conv_id,
                "bot_name": CUSTOMER_BOT_USERNAME,
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
@app.get("/api/stats/{conversation_id}", response_model=ConversationStats)
def get_conversation_stats(conversation_id: str):
   
    try:
        # Count total messages
        total_messages = collection.count_documents({"conversation_id": conversation_id})
        
        if total_messages == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No messages found for conversation_id: {conversation_id}"
            )
        
        # Count by role
        customer_messages = collection.count_documents({
            "conversation_id": conversation_id,
            "role": "customer"
        })
        
        salesperson_messages = collection.count_documents({
            "conversation_id": conversation_id,
            "role": "salesperson"
        })
        
        # Get first and last message (from ALL messages)
        first_msg = collection.find_one(
            {"conversation_id": conversation_id},
            sort=[("timestamp", 1)]
        )
        last_msg = collection.find_one(
            {"conversation_id": conversation_id},
            sort=[("timestamp", -1)]
        )
        
        # Calculate duration (from first to last message of entire conversation)
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
        result_data = scores_collection.find_one({"test_id": conversation_id})
        
        # Default values
        score = "N/A"
        english_level = "N/A"
        level_description = "N/A"
        
        # Extract evaluation results
        if result_data:
            score = result_data.get("score", "N/A")
            english_level = result_data.get("english_level", "N/A")
            level_description = result_data.get("assessment", "N/A")
        
        response_time = calculate_average_response_time(conversation_id)
        
        return {
            "conversation_id": conversation_id,
            "customer_name": CUSTOMER_BOT_USERNAME,
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
    uvicorn.run(app, host="10.10.20.111", port=8089, reload=True)