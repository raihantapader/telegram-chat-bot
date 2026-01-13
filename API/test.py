from fastapi import FastAPI, HTTPException
from models import Product  
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

MongoDB_Url = os.getenv("MONGODB_URI")
client = MongoClient(MongoDB_Url)
db = client['Raihan']  
products_collection = db['products']  

app = FastAPI()  # FastAPI instance

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Hello, Raihan! Welcome to FastAPI API Interface!"}

@app.post("/product")
def add_product(product: Product):
   
    existing_product = products_collection.find_one({"id": product.id})
    if existing_product:
        raise HTTPException(status_code=400, detail="Product with this ID already exists")


    product_data = product.dict()
    products_collection.insert_one(product_data)  
    return {"message": "Product added successfully", "product": product_data}


@app.get("/products")
def get_products():
    products = list(products_collection.find())  
    if not products:
        raise HTTPException(status_code=404, detail="No products found")
    
 
    for product in products:
        product['_id'] = str(product['_id'])  # Convert ObjectId to string
    return products
