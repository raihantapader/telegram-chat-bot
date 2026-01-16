import os
from pymongo import MongoClient
from dotenv import load_dotenv

from typing import List, Optional

# MongoDB setup
MongoDB_Url = os.getenv("MONGODB_URI")
client = MongoClient(MongoDB_Url)
db = client['Raihan']
collection = db['chat_bot']
scores_collection = db['evaluation_scores']


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

                    # Print the response time for each pair of messages
                    print(f"Salesperson message at {current_msg['timestamp']} -> "
                          f"Customer message at {next_msg['timestamp']} = {response_time_seconds:.2f} sec")

        if not response_times:
            return "N/A"

        # Calculate average response time
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


# Example: Use your actual conversation_id here
conversation_id = "3333"  # Replace with the actual conversation ID

# Call the function and get the average response time
avg_response_time = calculate_average_response_time(conversation_id)

# Print the final result
print(f"Average response time: {avg_response_time}")
