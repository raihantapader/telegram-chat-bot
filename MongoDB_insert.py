import pymongo
from bson import ObjectId
import os
from pymongo import MongoClient
from dotenv import load_dotenv

MONGODB_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGODB_URI)
db = client['Telegram_chatbot']  
collection = db["test"] 

#client = pymongo.MongoClient("mongodb://localhost:27017/")  
#db = client["Telegram_chatbot"] 
#collection = db["test"] 

def create_document():
    document = {
        "name": "John Doe",
        "age": 30,
        "address": "123 Main St"
    }
    result = collection.insert_one(document)
    print(f"Document inserted with _id: {result.inserted_id}")

def update_document():
    # Update the document where name is "John Doe"
    result = collection.update_one(
        {"name": "John Doe"},
        {"$set": {"age":80 }}  # Update the age field
    )
    print(f"Matched {result.matched_count} document(s), Modified {result.modified_count} document(s)")



if __name__ == "__main__":
    # Call CRUD functions
    create_document()  # Create a document

    update_document()  # Update a document
    