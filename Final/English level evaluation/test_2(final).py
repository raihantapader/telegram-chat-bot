import statistics
from pymongo import MongoClient
import openai
from datetime import datetime
import os
from dotenv import load_dotenv
import sys
import io
import re

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

load_dotenv()

MongoDB_Url = os.getenv("MONGODB_URI")  
client = MongoClient(MongoDB_Url)
db = client['Raihan']  # Database name
conversation_collection = db['chat_bot']  # Collection for conversations
scores_collection = db['evaluation_scores']  # Collection to store evaluation scores

openai.api_key = os.getenv("aluraagency_OPEPNAI_API_KEY")

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
    
    print("-"*60 + "\n")        
    print(f"[INFO] Total Salesperson(VA's) Messages Found: {len(messages)}")
    return messages


def evaluate_single_message(text):
    """
    - Evaluate a single message using GPT-3.5-turbo with high-accuracy expert prompt.
    - Optimized for Australian English and native-level business communication.
    - Returns a score between 0-100.
    """
    system_prompt = """
    You are a **Highly experienced English Language Assessment Expert** with over 20 years of experience in linguistics, grammar analysis, and professional communication assessment. You have evaluated thousands of business communications and are known for your precise, accurate, and fair evaluations. You evaluate correctness and english level of salesperson(Virtual assistant)'s messages in business contexts.
    
    ## YOUR EXPERTISE:
    - Expert in Australian English, British English, and American English standards
    - Specialized in evaluating sales and virtual assistant communications
    - Advanced grammar, syntax, and pragmatic analysis
    - Cross-cultural communication proficiency evaluation
    - Professional communication standards
    
    ## CONTEXT:
    You are evaluating messages from a **Australian salesperson/virtual assistant** who is communicating with **Australian native English-speaking clients**. The communication style should be:
    - Professional yet conversational (not overly formal)
    - Clear and customer-focused
    - Grammatically correct with natural flow
    - Culturally appropriate for Australian business context
    - Friendly, helpful, and engaging tone
    
    ## IMPORTANT NOTES ABOUT AUSTRALIAN ENGLISH:
    ✓ Australian English spelling is acceptable (e.g., "colour", "realise", "organisation")
    ✓ Casual, friendly tone is NORMAL and PROFESSIONAL in Australian business context
    ✓ Contractions are acceptable and natural (e.g., "we'll", "you're", "it's")
    ✓ Conversational expressions are appropriate (e.g., "no worries", "heaps", "reckon")
    ✓ Direct, straightforward communication is valued
    ✓ Slightly informal tone does NOT mean unprofessional
    
    ## YOUR TASK:
    Evaluate the following message and assign a score from 0 to 100 based on the following criteria:
    - Grammar
    - Sentence Structure
    - Fluency
    - Clarity
    
    EVALUATION CRITERIA (Apply rigorous standards):

    1. GRAMMAR ACCURACY (40 points):
       - Perfect tense usage and consistency (10 points)
       - Correct subject-verb agreement (10 points)
       - Proper punctuation and capitalization (10 points)
       - Correct use of articles (a, an, the) (5 points)
       - Proper preposition usage (5 points)

    2. SENTENCE STRUCTURE & CLARITY (30 points):
       - Well-formed, complete sentences (10 points)
       - Logical sentence flow and coherence (10 points)
       - Appropriate sentence complexity (5 points)
       - Clear and unambiguous meaning (5 points)

    3. FLUENCY & NATURALNESS (20 points):
       - Natural, conversational tone (appropriate for context) (10 points)
       - Smooth reading flow without awkwardness (10 points)

    4. VOCABULARY & WORD CHOICE (10 points):
       - Appropriate vocabulary for business context (5 points)
       - Correct word usage and spelling (5 points)

    SCORING GUIDELINES:
    1. **Excellent** (score 70-100): Outstanding English. Near-perfect fluency, very minor errors that don't affect clarity. Highly professional.
    2. **Good** (score 50-69): Good quality with minor errors. Clear and professional communication.
    3. **Medium** (score 30-49): Adequate English, some errors affecting clarity but still understandable.
    4. **Needs Improvement** (score below 30): Adequate English. Multiple errors affecting fluency. Problematic English. Major errors making comprehension difficult. Poor English with significant errors. Hard to understand. Incomprehensible or extremely poor English.

    Provide only the score and the corresponding level (e.g., "Score: 88, English Level: Excellent"). Do not provide any additional explanation or breakdown.

    IMPORTANT INSTRUCTIONS:
    - Be STRICT but FAIR in your evaluation
    - Consider the context: this is business/sales communication
    - Deduct points for each error, but consider severity
    - One major error should deduct more than multiple tiny errors
    - Respond with ONLY the numerical score (e.g., "87" or "72")
    - Do NOT include any explanation, just the number

    ANALYZE THE TEXT CAREFULLY AND PROVIDE YOUR EXPERT SCORE.
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[ 
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Text to evaluate:\n\n\"{text}\"\n\nProvide only the numerical score (0-100):"}
            ],
            max_tokens=10,
            temperature=0.1 
        )
        
        result = response.choices[0].message['content'].strip()
        
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

from datetime import datetime

def calculate_duration(start_time, end_time):
    """
    Calculate the duration between start_time and end_time in a human-readable format.
    Returns the duration in the format: 'X minutes Y seconds'.
    """
    duration_seconds = (end_time - start_time).seconds
    
    # Calculate minutes and seconds
    minutes = duration_seconds // 60
    seconds = duration_seconds % 60
    
    duration_str = f"{minutes} Min {seconds} Sec"
    
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
    for message in messages:
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
        "evaluation_time": datetime.now()  
    }
    
    existing_record = scores_collection.find_one({"test_id": test_id})
    if existing_record:
        
        scores_collection.update_one(
            {"test_id": test_id},
            {"$set": result_data}
        )
        print(f"[INFO] Updated evaluation for Test_ID {test_id}.")
    else:
        
        scores_collection.insert_one(result_data)
        print(f"[INFO] Stored new evaluation for Test_ID {test_id}.")
    
    print(f"\nTest_ID: {test_id}")
    print(f"Score: {round(average_score, 2)}/100")
    print(f"English Level: {english_level}")
    print(f"Assessment: {level_description}")
    print(f"Duration: {duration}")
    print("-"*60 + "\n")
    
    excellent = sum(1 for s in scores if s >= 70)
    good = sum(1 for s in scores if 50 <= s < 70)
    medium = sum(1 for s in scores if 30 <= s < 50)
    poor = sum(1 for s in scores if s < 30)
    
    print(f"Score Distribution of {len(scores)} Messages:")
    print(f"  🟢 Excellent (70-100): {excellent} messages ({round(excellent/len(scores)*100, 1)}%)")
    print(f"  🟡 Good (50-69):       {good} messages ({round(good/len(scores)*100, 1)}%)")
    print(f"  🟠 Medium (30-49):     {medium} messages ({round(medium/len(scores)*100, 1)}%)")
    print(f"  🔴 Poor (0-29):        {poor} messages ({round(poor/len(scores)*100, 1)}%)")
    print("-"*60 + "\n")
    
    return result_data


def main():
    test_id = "96369"  # Define the Test_ID you want to evaluate
    result = analyze_salesperson_texts(test_id)
    
    if result:
        pass 

if __name__ == "__main__":
    main()
