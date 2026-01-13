
from fastapi import FastAPI
from models import product

import os
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

app = FastAPI()  # app is object(create object for FastAPI)

@app.get("/")  # HTTP Get method for the root endpoint
def read_root():
    return {"message": "Hello, Raihan?"}

products = [
    product(id=1, name="phone", price=199.99, description="A smartphone", quantity=50),
    product(id=2, name="laptop", price=599.99, description="A laptop computer", quantity=25),
    product(id=3, name="tablet", price=299.99, description="A tablet device", quantity=30),
    product(id=5, name="watch", price=199.99, description="A smartwatch", quantity=40),
    product(id=6, name="headphones", price=149.99, description="Wireless headphones", quantity=60)
]
    

@app.get("/products")  # Fetching all records
def read_products():
    # DB connection
    #db = session()
    # query to fetch all products
    #db.query(product).all ()
    return products


@app.get("/product/{id}")  # Fatching individual record
def get_procuct_by_id(id: int):
    for product in products:
        if product.id == id:
            return product
    return "Product not found"


@app.post("/product")
def add_product(product: product):
    products.append(product)
    return product


@app.put("/product/{id}")
def update_product(id: int, product: product):
    for i in range(len(products)):
        if products[i].id == id:
            products[i] = product
            return "Product updated successfully"
    return "Product not found"


@app.delete("/product/{id}")
def delete_product(id: int):
    for i in range(len(products)):
        if products[i].id == id:
            del products[i]
            return "Product deleted successfully"
    return "Product not found"
