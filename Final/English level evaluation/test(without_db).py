# salesperson_english_evaluator.py

import statistics
from pymongo import MongoClient
import openai
from datetime import datetime
import os
from dotenv import load_dotenv
import sys
import io

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

load_dotenv()

MongoDB_Url = os.getenv("MONGODB_URI")  
client = MongoClient(MongoDB_Url)
db = client['Raihan']  # Database name
collection = db['chat_bot']  # Collection name to store conversations

# OpenAI API Setup
openai.api_key = os.getenv("aluraagency_OPEPNAI_API_KEY")


def extract_salesperson_messages():
    """
    Extract all salesperson messages from MongoDB, sorted by timestamp.
    Returns a list of text messages only.
    """
    # print("[INFO] Extracting salesperson messages from database...")
    
    # Query: get only salesperson role from conversation 563964, sorted by timestamp
    salesperson_data = collection.find(
        {
            "conversation_id": "281101", 
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
    
    print(f"[INFO] Total Salesperson(VA's) Messages Found: {len(messages)}")
    return messages


def evaluate_single_message(text):
    """
    Evaluate a single message using GPT-3.5-turbo with high-accuracy expert prompt.
    Returns a score between 0-100.
    """
    
    system_prompt = """
You are a highly experienced English language expert with over 20 years of experience in linguistics, grammar analysis, and professional communication assessment. You have evaluated thousands of business communications and are known for your precise, accurate, and fair evaluations.

Your expertise includes:
- Advanced grammar and syntax analysis
- Professional communication standards
- Business English proficiency assessment
- Natural language fluency evaluation
- Written communication clarity assessment

TASK:
Evaluate the English quality of the provided text with EXTREME PRECISION and provide ONLY a numerical score from 0 to 100.

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
- 95-100: EXCEPTIONAL - Perfect or near-perfect English. Native-level fluency. Zero errors. Professional quality.
- 85-94:  EXCELLENT - Outstanding English. Very minor errors that don't affect clarity. Highly professional.
- 75-84:  VERY GOOD - Strong English. Few minor errors. Clear and professional communication.
- 65-74:  GOOD - Competent English. Some errors but message is clear. Acceptable professional standard.
- 55-64:  FAIR - Adequate English. Multiple errors affecting fluency. Meaning still understandable.
- 45-54:  BELOW AVERAGE - Weak English. Significant errors affecting clarity. Needs improvement.
- 35-44:  POOR - Problematic English. Major errors making comprehension difficult.
- 25-34:  VERY POOR - Severely flawed English. Very hard to understand.
- 0-24:   UNACCEPTABLE - Incomprehensible or extremely poor English.

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
            temperature=0.2  # Lower temperature for more consistent scoring
        )
        
        result = response.choices[0].message['content'].strip()
        
        # Extract numerical score
        import re
        score_match = re.search(r'\d+', result)
        if score_match:
            score = int(score_match.group())
            # Ensure score is within valid range
            score = max(0, min(100, score))
            return score
        else:
            print(f"[WARNING] Could not parse score from: {result}")
            return 50  # Default score
            
    except Exception as e:
        print(f"[ERROR] Failed to evaluate message: {str(e)}")
        return 50  # Default score on error


def analyze_all_salesperson_texts():
    """
    Main analysis function:
    1. Extract all salesperson messages
    2. Evaluate each message
    3. Calculate overall score
    4. Determine English level with color indicator
    """
    
    # Step 1: Extract messages
    messages = extract_salesperson_messages()
    
    if not messages:
        print("[ERROR] No salesperson messages found in database!")
        return None
    
    # Step 2: Evaluate each message
    #print(f"\n[INFO] Evaluating {len(messages)} messages with expert analysis...")
    #print("[INFO] This may take a few moments...\n")
    
    scores = []
    
    for i, message in enumerate(messages, 1):
        text = message["text"]
        
        # Show progress
       # if i % 10 == 0 or i == 1:
           # print(f"[PROGRESS] Evaluating message {i}/{len(messages)}...")
        
        # Evaluate the message
        score = evaluate_single_message(text)
        scores.append(score)
    
    # Step 3: Calculate overall score
    if scores:
        average_score = statistics.mean(scores)
    else:
        average_score = 0
    
    # Step 4: Determine English Level with color indicator based on average score
    if average_score >= 70:
        english_level = "🟢 Excellent"  # Strong, professional English
        level_description = "Strong conversion potential"
    elif average_score >= 50:
        english_level = "🟡 Good"  # Good potential, build value
        level_description = "Good potential, minor improvements needed"
    elif average_score >= 30:
        english_level = "🟠 Medium"  # Needs improvement, re-engage
        level_description = "Needs improvement, re-engage"
    else:
        english_level = "🔴 Needs Improvement"  # Poor fit, consider re-qualifying
        level_description = "Poor fit, consider re-qualifying"
    
    # Step 5: Display final results (clean output as requested)
   # print("-"*60 + "\n")
   # print("EVALUATION COMPLETE".center(60))
   # print("-"*60 + "\n")
    print(f"\nScore: {round(average_score, 2)}/100")
    print(f"English Level: {english_level}")
    print(f"Assessment: {level_description}")
    print("-"*60 + "\n")
    
    return {
        "total_messages": len(messages),
        "overall_score": round(average_score, 2),
        "english_level": english_level,
        "level_description": level_description,
        "individual_scores": scores
    }


def main():
    """
    Main execution function
    """
    #print("\n" + "="*60)
    #print("SALESPERSON ENGLISH QUALITY ANALYZER".center(60))
   # print("="*60 + "\n")
   # print("-"*60 + "\n")
    
    # Analyze all salesperson texts
    result = analyze_all_salesperson_texts()
    
    if result:
            scores = result["individual_scores"]
            
            # Score distribution
            excellent = sum(1 for s in scores if s >= 70)
            good = sum(1 for s in scores if 50 <= s < 70)
            medium = sum(1 for s in scores if 30 <= s < 50)
            poor = sum(1 for s in scores if s < 30)
            
            print(f"\nScore Distribution of {len(scores)} Messages:")
            print(f"  🟢 Excellent (70-100): {excellent} messages ({round(excellent/len(scores)*100, 1)}%)")
            print(f"  🟡 Good (50-69):       {good} messages ({round(good/len(scores)*100, 1)}%)")
            print(f"  🟠 Medium (30-49):     {medium} messages ({round(medium/len(scores)*100, 1)}%)")
            print(f"  🔴 Poor (0-29):        {poor} messages ({round(poor/len(scores)*100, 1)}%)")
            #print("-"*60 + "\n")
    else:
        print("\n[ERROR] Analysis failed. Please check your database connection and data.")


if __name__ == "__main__":
    main()