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

# MongoDB connection - same as monitor
MongoDB_Url = os.getenv("DB_URI")
client = MongoClient(MongoDB_Url)
db = client['Raihan']
chat_collection = db['telegram_chats']

app = FastAPI(title="Telegram Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MessageOutput(BaseModel):
    chat_id: Optional[int] = None
    role: Optional[str] = None
    name: Optional[str] = None
    text: Optional[str] = None
    timestamp: Optional[datetime] = None


@app.get("/")
def root():
    return {
        "message": "Telegram Chat API",
        "endpoints": {
            "GET /api/messages": "Get all messages sorted by timestamp",
            "GET /api/messages/{chat_id}": "Get messages by chat_id",
            "GET /api/stats": "Get statistics"
        }
    }


@app.get("/api/messages")
def get_all_messages():
    """Get all messages sorted by timestamp"""
    try:
        messages = list(chat_collection.find({}).sort("timestamp", 1))
        
        if not messages:
            return {"total": 0, "messages": []}
        
        result = []
        for msg in messages:
            result.append({
                "chat_id": msg.get("chat_id"),
                "role": msg.get("role"),
                "name": msg.get("name"),
                "text": msg.get("text"),
                "timestamp": msg.get("timestamp")
            })
        
        return {"total": len(result), "messages": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@app.get("/api/messages/{chat_id}")
def get_messages_by_chat_id(chat_id: int):
    """Get messages by chat_id sorted by timestamp"""
    try:
        messages = list(chat_collection.find(
            {"chat_id": chat_id}
        ).sort("timestamp", 1))
        
        if not messages:
            return {"total": 0, "messages": []}
        
        result = []
        for msg in messages:
            result.append({
                "chat_id": msg.get("chat_id"),
                "role": msg.get("role"),
                "name": msg.get("name"),
                "text": msg.get("text"),
                "timestamp": msg.get("timestamp")
            })
        
        return {"total": len(result), "messages": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@app.get("/api/stats")
def get_stats():
    """Get statistics"""
    try:
        total = chat_collection.count_documents({})
        sender = chat_collection.count_documents({"role": "sender"})
        receiver = chat_collection.count_documents({"role": "receiver"})
        
        return {
            "total_messages": total,
            "sent_by_you": sender,
            "received": receiver
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")

if __name__ == "__main__":
    print("="*50)
    print("TELEGRAM CHAT API".center(50))
    print("="*50)
    print("\nEndpoints:")
    print("  GET    /api/messages           - All messages")
    print("  GET    /api/messages/{chat_id} - By chat_id")
    print("  GET    /api/stats              - Statistics")
    print("  DELETE /api/messages           - Delete all")
    print("="*50)
    print("\nServer: http://10.10.20.111:8090")
    print("Docs: http://10.10.20.111:8090/docs")
    print("="*50 + "\n")
    
    uvicorn.run(app, host="10.10.20.111", port=8090, reload=True)