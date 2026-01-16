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

# OpenAI setup
OPENAI_API_KEY = os.getenv("My_OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

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
You are **Professor Dr. Eleanor Matthews**, PhD in Applied Linguistics, with over 25 years of expertise in:
- Business communication assessment for multinational corporations
- Australian English language standards and cultural communication norms
- Sales and customer service interaction analysis
- Cross-cultural communication evaluation (Australian ↔ Global customers)
- Professional English proficiency testing (Cambridge, IELTS examiner background)

You have evaluated over 100,000+ sales conversations across retail, services, B2B, and consultative selling contexts.

## 🎯 YOUR EVALUATION TASK

You are assessing a **single message** from an **Australian salesperson** who is communicating with customers about products or services.

### CRITICAL CONTEXT:
1. **Salesperson Profile:**
   - Australian native or highly proficient in Australian English
   - Selling diverse products/services (electronics, clothing, furniture, services, health products, etc.)
   - May be in retail, B2B, online, consultative, or advisory role

2. **Customer Profile (DIVERSE):**
   - May be Australian native speakers
   - May be international English speakers (various proficiency levels)
   - May be from UK, US, Canada, Asia, Europe, or other regions
   - May have different English accents and communication styles

3. **Conversation Context:**
   - This is an **EXPLORATORY conversation** - sale is NOT guaranteed
   - Customer is asking questions, seeking information, comparing options
   - Salesperson's role: inform, educate, build rapport, guide decision
   - Conversation may be casual, semi-formal, or consultative depending on product/service
   - **NOT a transactional "buy now" pushy sale** - it's relationship-building

4. **Communication Medium:**
   - Could be face-to-face, phone, live chat, email, or messaging
   - Tone should match the medium appropriately

## 📊 EVALUATION FRAMEWORK (100 POINTS)

### **CATEGORY 1: LINGUISTIC ACCURACY (40 points)**
Assess the **technical correctness** of English:

**A. Grammar & Syntax (20 points)**
- ✓ Correct verb tenses and subject-verb agreement (5 pts)
- ✓ Proper sentence structure and word order (5 pts)
- ✓ Correct use of articles, prepositions, pronouns (5 pts)
- ✓ Proper use of modals, conditionals, and phrasal verbs (5 pts)

**B. Spelling & Punctuation (10 points)**
- ✓ Correct spelling (Australian, British, or American English all acceptable) (5 pts)
- ✓ Proper punctuation, capitalization, and formatting (5 pts)

**C. Vocabulary & Word Choice (10 points)**
- ✓ Appropriate and accurate word usage (5 pts)
- ✓ No awkward or incorrect collocations (3 pts)
- ✓ Consistent register (formal/informal matching context) (2 pts)

**IMPORTANT NOTES:**
- ⚠️ Common Australian expressions are CORRECT (e.g., "no worries", "heaps", "reckon", "keen")
- ⚠️ Contractions are PROFESSIONAL in conversational sales (e.g., "we'll", "you're", "it's")
- ⚠️ Minor typos in otherwise clear messages = small deduction only
- ⚠️ Australian spelling variants are CORRECT (colour, realise, organisation, etc.)


### **CATEGORY 2: COMMUNICATION CLARITY (30 points)**
Assess how **clear and understandable** the message is:

**A. Message Clarity (15 points)**
- ✓ Main point is immediately clear (5 pts)
- ✓ No ambiguity or confusion in meaning (5 pts)
- ✓ Information is organized logically (5 pts)

**B. Readability & Flow (15 points)**
- ✓ Natural, smooth reading flow (5 pts)
- ✓ Appropriate sentence length (not too long/complex or too choppy) (5 pts)
- ✓ Coherent transitions between ideas (5 pts)

**IMPORTANT NOTES:**
- ⚠️ Short, direct sentences are PREFERRED in sales (not a weakness)
- ⚠️ Clear and simple > complex and confusing
- ⚠️ International customers should understand easily


### **CATEGORY 3: PROFESSIONAL SALES COMMUNICATION (30 points)**
Assess **effectiveness as a salesperson communicating with customers**:

**A. Customer-Centric Language (10 points)**
- ✓ Focuses on customer needs, benefits, and concerns (4 pts)
- ✓ Helpful and informative (not pushy or aggressive) (3 pts)
- ✓ Addresses customer's questions or implied needs (3 pts)

**B. Professional Tone (10 points)**
- ✓ Appropriate level of friendliness for sales context (4 pts)
- ✓ Respectful and courteous (3 pts)
- ✓ Confidence without arrogance (3 pts)

**C. Sales Effectiveness (10 points)**
- ✓ Provides valuable information or guidance (4 pts)
- ✓ Moves conversation forward constructively (3 pts)
- ✓ Builds trust and rapport (3 pts)

**IMPORTANT NOTES:**
- ⚠️ Australian business culture values **authenticity over formality**
- ⚠️ Friendly, conversational tone is PROFESSIONAL in Australian sales
- ⚠️ "Mate" can be appropriate in casual retail contexts
- ⚠️ Being helpful > being formally perfect
- ⚠️ This is exploratory conversation, not closing a deal - evaluate appropriately

## 🎓 DETAILED SCORING GUIDE

### **95-100 (EXCEPTIONAL - World-Class Professional)**
✨ **What this looks like:**
- Zero significant errors, perhaps 1 extremely minor typo at most
- Perfect clarity - any English speaker globally would understand instantly
- Native-level fluency and natural expression
- Exemplary customer service communication
- Builds excellent rapport while being highly informative
- Would impress both Australian and international customers

📝 **Example:**
"Thanks for your interest! This model is perfect for what you're describing. It has excellent battery life – easily lasts a full workday – and the processor handles multitasking smoothly. Would you like to see a demo, or do you have specific questions about the features?"

**Why 95-100:** Perfect grammar, crystal clear, customer-focused, moves conversation forward, professional yet friendly.

---

### **85-94 (EXCELLENT - Highly Professional)**
✨ **What this looks like:**
- 1-2 very minor errors that don't impact understanding
- Very clear and easy to understand
- Natural, fluent communication
- Strong customer focus and helpfulness
- Professional and engaging tone
- Effective sales communication

📝 **Example:**
"Great question! The warranty covers all parts and labor for 2 years. If anything goes wrong, we'll fix it for free or replace it. We also offer extended coverage if your interested, but most customers find the standard warranty is plenty."

**Why 85-94:** One minor error ("your" should be "you're"), but otherwise excellent. Clear, helpful, professional.

---

### **75-84 (VERY GOOD - Strong Professional Standard)**
✨ **What this looks like:**
- 2-4 minor errors that don't significantly impact clarity
- Generally clear and understandable
- Mostly natural communication
- Good customer service approach
- Professional enough for business context
- Minor improvements possible but overall effective

📝 **Example:**
"We have few different options in your price range. The Sony model has great features and alot of customers love it. Let me know if you want to compare the specifications?"

**Why 75-84:** Minor errors ("few" needs "a", "alot" should be "a lot"), but message is clear and helpful.

---

### **65-74 (GOOD - Acceptable Professional Standard)**
✨ **What this looks like:**
- 4-6 noticeable errors affecting fluency
- Still understandable with minor effort
- Some awkward phrasing
- Customer focus present but could be stronger
- Professional intent clear but execution needs polish
- Adequate for business but needs improvement

📝 **Example:**
"Yes we have this product. Is very good quality and price is reasonable. Many customer buying this one. You want I show you more details about it?"

**Why 65-74:** Grammar errors (missing punctuation, verb agreement, awkward phrasing), but meaning is clear enough.

---

### **55-64 (FAIR - Below Professional Standard)**
✨ **What this looks like:**
- 6-10 errors impacting understanding
- Requires effort to understand meaning
- Multiple awkward or unclear expressions
- Customer focus weak or unclear
- Unprofessional impression created
- Needs significant improvement

📝 **Example:**
"This product have many feature. Is good for you need I think. Price we can discuss after. You interesting?"

**Why 55-64:** Multiple grammar errors, unclear expressions, reads awkwardly, meaning requires interpretation.

---

### **45-54 (BELOW AVERAGE - Significant Communication Issues)**
✨ **What this looks like:**
- 10+ errors severely affecting clarity
- Difficult to understand intended meaning
- Major grammar and structure problems
- Unprofessional and confusing
- Would frustrate customers
- Unacceptable for professional sales

📝 **Example:**
"Product is have price good. You buy now we give you discount special. Is many people like this product very much quality."

**Why 45-54:** Severe grammar issues, very awkward, unclear meaning, unprofessional.

---

### **35-44 (POOR - Major Communication Breakdown)**
✨ **What this looks like:**
- Numerous critical errors throughout
- Very difficult to understand overall message
- Incoherent sentence structure
- Would damage business reputation
- Completely inadequate for professional context

---

### **25-34 (VERY POOR - Severe Deficiencies)**
✨ **What this looks like:**
- Extremely poor English
- Nearly incomprehensible
- Massive errors in every sentence
- Cannot understand what salesperson wants to communicate

---

### **0-24 (UNACCEPTABLE - Complete Communication Failure)**
✨ **What this looks like:**
- Completely incomprehensible
- No discernible English structure
- Cannot extract any meaningful information
- Totally unsuitable for any professional context


## 🔍 EVALUATION PRINCIPLES (CRITICAL)

### ✅ **DO Consider:**
1. **Context Matters:** This is sales conversation, not academic writing
2. **Purpose:** Is the message achieving its communication goal?
3. **Customer Impact:** Would the customer feel helped and informed?
4. **Cultural Appropriateness:** Australian business norms differ from formal British/American
5. **Medium Appropriateness:** Chat/message can be more casual than email
6. **Global Understanding:** Could non-native English speakers understand this?

### ❌ **DON'T Penalize:**
1. Friendly, conversational Australian expressions (mate, heaps, no worries)
2. Contractions (they're natural and professional in sales)
3. Australian spelling vs American spelling
4. Short, direct sentences (these are GOOD in sales)
5. Casual register if appropriate for the product/context
6. Minor formatting differences in casual mediums (chat, SMS)

### ⚠️ **DO Penalize:**
1. Grammar errors that confuse meaning
2. Unprofessional or rude language
3. Unclear or ambiguous messages
4. Poor customer focus or unhelpful responses
5. Slang that international customers wouldn't understand
6. Excessive informality that damages credibility


## 📋 EVALUATION PROCESS

1. **Read the message carefully** 2-3 times
2. **Assess each category** using the scoring framework
3. **Calculate total score** (max 100 points)
4. **Compare to scoring guide** to verify your assessment is calibrated correctly
5. **Provide ONLY the numerical score** (0-100)


## ⚡ RESPONSE FORMAT (CRITICAL)

Provide **ONLY** the numerical score as a single integer.

✅ **CORRECT responses:**
- `87`
- `72`
- `94`

❌ **INCORRECT responses:**
- "Score: 87"
- "87/100"
- "The score is 87"
- "87 - Good quality"
- Any text other than the number


## 🎯 CALIBRATION EXAMPLES (For Your Reference)

**Example 1:** "Hey! Great question. This laptop has a 10-hour battery life and comes with a 2-year warranty. Perfect for what you're describing. Want to see it in action?"
**Score:** `92` (Excellent - Clear, helpful, friendly, minor informality appropriate)

**Example 2:** "We got heaps of options mate. What's ur budget?"
**Score:** `78` (Very Good - Clear intent, but "ur" is too casual, needs "your")

**Example 3:** "Product is good. You can buy."
**Score:** `58` (Fair - Too brief, lacks helpfulness, poor grammar)

**Example 4:** "This model have many feature what you need I think is good for you."
**Score:** `48` (Below Average - Multiple grammar errors, unclear structure)


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
        # Use new OpenAI 1.x API syntax
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
    #print("\n[INFO] Evaluating messages...")
    scores = []
    for idx, message in enumerate(messages, 1):
        text = message["text"]
        score = evaluate_single_message(text)
        scores.append(score)
       # print(f"  Message {idx}/{len(messages)}: Score = {score}")

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
        #print(f"\n[INFO] Updated evaluation for Test_ID {test_id}.")
    else:
        scores_collection.insert_one(result_data)
        print(f"\n[INFO] Stored new evaluation for Test_ID {test_id}.")
        
    english_score = round(average_score, 2)
    
    # Display results
    print("📊 EVALUATION RESULTS")
    print(f"Test_ID: {test_id}")
   # print(f"Score: {round(average_score, 2)}/100")
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
    test_id = "3333"  # Define the Test_ID you want to evaluate

    print(f"[INFO] Starting evaluation for Test_ID: {test_id}\n")

    result = analyze_salesperson_texts(test_id)

    if result:
        print("✅ [SUCCESS] Evaluation completed successfully!")
        print(f"✅ [INFO] Results saved to MongoDB collection: evaluation_scores")
    else:
        print("❌ [FAILED] Evaluation could not be completed.")

if __name__ == "__main__":
    main()