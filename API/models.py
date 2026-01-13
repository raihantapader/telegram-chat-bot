from pydantic import BaseModel

# Product model
class Product(BaseModel):
    id: int
    name: str
    price: float
    description: str
    quantity: int
