import statistics
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv
import sys
import io
import re
from openai import OpenAI
import random

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

load_dotenv()

# MongoDB setup
MongoDB_Url = os.getenv("MONGODB_URI")
mongo_client = MongoClient(MongoDB_Url)
db = mongo_client['Raihan']  # Database name
conversation_collection = db['chat_bot']  # Collection for conversations
scores_collection = db['evaluation_scores']  # Collection to store evaluation scores
test_collection = db['active_test_ids']  # Collection for active test ids

# OpenAI setup
OPENAI_API_KEY = os.getenv("My_OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)


def get_latest_test_id():
    """Get the most recent active test_id from database"""
    try:
        latest_test = test_collection.find_one(
            {"status": "active"},
            sort=[("created_at", -1)]  # Sorting by creation date in descending order
        )
        
        if latest_test:
            test_id = latest_test['test_id']
            print(f"✅ Retrieved latest Test ID from database: {test_id}")
            return test_id
        else:
            print("⚠️  No active test_id found in database. Using default.")
            return "default"
    except Exception as e:
        print(f"❌ Error retrieving test_id: {e}")
        return "default"


def extract_salesperson_messages(test_id):
    """
    Extract all salesperson messages from MongoDB for a specific Test_ID, sorted by timestamp.
    Returns a list of text messages only.
    """
    salesperson_data = conversation_collection.find(
        {
            "conversation_id": test_id,
            "role": "salesperson"
        }
    ).sort("timestamp", 1)

    # Extract only the text field
    messages = []
    for message in salesperson_data:
        if "text" in message and message["text"].strip():
            messages.append({
                "text": message["text"],
                "timestamp": message.get("timestamp", "N/A")
            })

    # Improved logging
    print(f"[INFO] Fetched {len(messages)} salesperson messages for test_id: {test_id}")
    
    if not messages:
        print(f"[INFO] No salesperson messages found for test_id: {test_id}.")
        
    return messages


def evaluate_single_message(text):
    """
    - Evaluate a single message using GPT-3.5-turbo with high-accuracy expert prompt.
    - Optimized for Australian English and native-level business communication.
    - Returns a score between 0-100.
    """
    system_prompt = """
You are **Professor Dr. Eleanor Matthews**, PhD in Applied Linguistics, with over 25 years of experience evaluating professional communication.

## 🧠 FINAL REMINDER

You are evaluating **professional sales communication effectiveness** in an **Australian business context** with **diverse global customers**.

- Be **fair but rigorous**
- Consider **real-world business impact**
- Account for **cultural communication norms**
- Focus on **clarity and customer experience**
- Reward **effective communication**, not just grammatical perfection

Now evaluate the message below and provide ONLY the score (0-100):
"""

    try:
        # Use OpenAI 1.x API syntax
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[ 
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Text to evaluate:\n\n\"{text}\"\n\nProvide only the numerical score (0-100):"}
            ],
            max_tokens=10,
            temperature=0.0
        )
        # Access response with new syntax
        result = response.choices[0].message.content.strip()

        # Extract numerical score
        score_match = re.search(r'\d+', result)
        if score_match:
            score = int(score_match.group())
            # Ensure score is within valid range
            score = max(0, min(100, score))
            return score
        else:
            print(f"[WARNING] Could not parse score from: {result}")
            return 50

    except Exception as e:
        print(f"[ERROR] Failed to evaluate message: {str(e)}")
        return 50


def calculate_duration(start_time, end_time):
    """
    Calculate the duration between start_time and end_time in a human-readable format.
    Returns the duration in the format: 'X minutes Y seconds'.
    """
    duration_seconds = (end_time - start_time).seconds

    # Calculate minutes and seconds
    hours = duration_seconds // 3600
    duration_seconds %= 3600
    minutes = duration_seconds // 60
    seconds = duration_seconds % 60

    duration_str = f"{hours} Hr {minutes} Min {seconds} Sec"
    return duration_str


def analyze_salesperson_texts(test_id):
    """
    Main analysis function for a given Test_ID:
    1. Extract all salesperson messages.
    2. Evaluate each message.
    3. Calculate overall score and English level.
    4. Determine conversation duration based on timestamp.
    """

    # Step 1: Extract messages
    messages = extract_salesperson_messages(test_id)

    if not messages:
        print("[ERROR] No salesperson messages found for the given Test_ID!")
        return None

    # Step 2: Evaluate each message
    scores = []
    for idx, message in enumerate(messages, 1):
        text = message["text"]
        score = evaluate_single_message(text)
        scores.append(score)

    # Step 3: Calculate overall score
    if scores:
        average_score = round(statistics.mean(scores), 2)
    else:
        average_score = 0

    # Step 4: Determine English level based on score
    if average_score >= 70:
        english_level = "🟢 Excellent"
        level_description = "Strong conversion potential"
    elif average_score >= 50:
        english_level = "🟡 Good"
        level_description = "Good potential, minor improvements needed"
    elif average_score >= 30:
        english_level = "🟠 Medium"
        level_description = "Needs improvement, re-engage"
    else:
        english_level = "🔴 Needs Improvement"
        level_description = "Poor English, consider re-qualifying"

    # Step 5: Calculate start and end times, and duration
    start_time = messages[0]["timestamp"]
    end_time = messages[-1]["timestamp"]
    duration = calculate_duration(start_time, end_time)

    # Step 6: Store results in the evaluation_scores collection
    result_data = {
        "test_id": test_id,
        "score": f"{average_score}/100",
        "english_level": english_level,
        "assessment": level_description,
        "start_time": start_time,
        "end_time": end_time,
        "duration": duration,
        "total_messages": len(messages),
        "individual_scores": scores,
        "evaluation_time": datetime.now()
    }

    existing_record = scores_collection.find_one({"test_id": test_id})
    if existing_record:
        scores_collection.update_one(
            {"test_id": test_id},
            {"$set": result_data}
        )
    else:
        scores_collection.insert_one(result_data)
        print(f"\n[INFO] Stored new evaluation for Test_ID {test_id}.")
        
    english_score = round(average_score, 2)
    
    # Display results
    print("📊 EVALUATION RESULTS")
    print(f"Test_ID: {test_id}")
    print(f"Score: {english_score}/100")
    print(f"English Level: {english_level}")
    print(f"Assessment: {level_description}")
    print(f"Duration: {duration}")
    print(f"Total Messages: {len(messages)}")
    print("-"*60)

    # Score distribution
    excellent = sum(1 for s in scores if s >= 70)
    good = sum(1 for s in scores if 50 <= s < 70)
    medium = sum(1 for s in scores if 30 <= s < 50)
    poor = sum(1 for s in scores if s < 30)

    print(f"\n📈 Score Distribution of {len(scores)} Messages:")
    print(f"  🟢 Excellent (70-100): {excellent} messages ({round(excellent/len(scores)*100, 1)}%)")
    print(f"  🟡 Good (50-69):       {good} messages ({round(good/len(scores)*100, 1)}%)")
    print(f"  🟠 Medium (30-49):     {medium} messages ({round(medium/len(scores)*100, 1)}%)")
    print(f"  🔴 Poor (0-29):        {poor} messages ({round(poor/len(scores)*100, 1)}%)")
    print("="*60 + "\n")

    return result_data


def main():
    """
    Main execution function
    """  
    test_id = get_latest_test_id()  # Dynamically get the latest test_id

    print(f"[INFO] Starting evaluation for Test_ID: {test_id}\n")

    result = analyze_salesperson_texts(test_id)

    if result:
        print("✅ [SUCCESS] Evaluation completed successfully!")
        print(f"✅ [INFO] Results saved to MongoDB collection: evaluation_scores")
    else:
        print("❌ [FAILED] Evaluation could not be completed.")

if __name__ == "__main__":
    main()
