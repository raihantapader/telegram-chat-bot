import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn
from pymongo import MongoClient
from datetime import datetime

load_dotenv()

# MongoDB connection setup
MongoDB_Url = os.getenv("MONGODB_URI")
mongo_client = MongoClient(MongoDB_Url)
db = mongo_client['Raihan']
test_collection = db['Test_ID']

app = FastAPI(title="Multi-Bot Test Controller API")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Bot tokens for all 5 customer bots
bot_tokens = {
    "bot_1": os.getenv("TELEGRAM_BOT_1_TOKEN"),  # @Cust0m3rBot
    "bot_2": os.getenv("TELEGRAM_BOT_2_TOKEN"),  # @Cust0m4rBot
    "bot_3": os.getenv("TELEGRAM_BOT_3_TOKEN"),  # @Cust0m5rBot
    "bot_4": os.getenv("TELEGRAM_BOT_4_TOKEN"),  # @Cust0m6rBot
    "bot_5": os.getenv("TELEGRAM_BOT_5_TOKEN"),  # @Cust0m7rBot
}

# Your personal chat ID (where messages will be sent)
YOUR_CHAT_ID = os.getenv("YOUR_TELEGRAM_CHAT_ID")  # Get from @userinfobot


def send_start_command_to_bot(token, test_id, bot_name):
    """
    Send /start command with test_id to a specific bot
    """
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # Message that triggers the bot with test_id
    message = f"/start {test_id}"
    
    payload = {
        "chat_id": YOUR_CHAT_ID,
        "text": message
    }
    
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print(f"✅ Test ID {test_id} sent to {bot_name}")
            return True
        else:
            print(f"❌ Failed to send to {bot_name}: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error sending to {bot_name}: {e}")
        return False


@app.get("/send_testid/{test_id}")
async def send_testid_to_all_bots(test_id: str):
    """
    Endpoint triggered when link is clicked.
    Sends test_id to all 5 customer bots.
    """
    print(f"\n{'='*70}")
    print(f"📤 SENDING TEST ID: {test_id} TO ALL BOTS")
    print(f"{'='*70}\n")
    
    results = {}
    success_count = 0
    
    # Send to all bots
    for bot_name, token in bot_tokens.items():
        if token:
            success = send_start_command_to_bot(token, test_id, bot_name)
            results[bot_name] = "sent" if success else "failed"
            if success:
                success_count += 1
        else:
            results[bot_name] = "no_token"
            print(f"⚠️  {bot_name}: Token not found in .env")
    
    # Store in MongoDB
    test_data = {
        "test_id": test_id,
        "status": "active",
        "bots_triggered": success_count,
        "bot_results": results,
        "timestamp": datetime.utcnow()
    }
    
    test_collection.insert_one(test_data)
    
    print(f"\n{'='*70}")
    print(f"✅ SUMMARY: {success_count}/{len(bot_tokens)} bots triggered successfully")
    print(f"{'='*70}\n")
    
    return {
        "status": "success",
        "test_id": test_id,
        "bots_triggered": success_count,
        "total_bots": len(bot_tokens),
        "results": results,
        "message": f"Test ID {test_id} sent to {success_count} bots"
    }


@app.get("/test_ids")
async def get_all_test_ids():
    """
    Retrieve all test_ids with their status
    """
    test_data_list = list(test_collection.find({}).sort("timestamp", -1))
    
    result = []
    for test_data in test_data_list:
        test_data["_id"] = str(test_data["_id"])
        result.append(test_data)
    
    return {
        "total_tests": len(result),
        "test_ids": result
    }


@app.get("/test_id/{test_id}")
async def get_test_details(test_id: str):
    """
    Get details of a specific test_id
    """
    test_data = test_collection.find_one({"test_id": test_id})
    
    if not test_data:
        raise HTTPException(status_code=404, detail=f"Test ID {test_id} not found")
    
    test_data["_id"] = str(test_data["_id"])
    return test_data


if __name__ == "__main__":
    print("="*70)
    print("MULTI-BOT TEST CONTROLLER API".center(70))
    print("="*70)
    print("\nEndpoints:")
    print("  GET /send_testid/{test_id}  - Trigger all bots with test_id")
    print("  GET /test_ids               - Get all test IDs")
    print("  GET /test_id/{test_id}      - Get specific test details")
    print("="*70)
    print("\nServer running at: http://10.10.20.111:7000")
    print("="*70 + "\n")
    
    uvicorn.run(app, host="10.10.20.111", port=7000, reload=True)
