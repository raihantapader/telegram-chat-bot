
import os
import hashlib
import jwt
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pydantic import BaseModel, EmailStr
from typing import Optional
from bson import ObjectId
from dotenv import load_dotenv
import uvicorn
# from fastapi import APIRouter

load_dotenv()

# MongoDB connection
MongoDB_Url = os.getenv("DB_URI")
client = MongoClient(MongoDB_Url)
db = client['Raihan']
admins_collection = db['admins']

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your_super_secret_key_2026")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24  # Token expires in 24 hours

# FastAPI app
# router = APIRouter()
app = FastAPI(title="Admin Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models

class AddAdmin(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    password: str


class AdminLogin(BaseModel):
    email: EmailStr
    password: str


class AdminEmail(BaseModel):
    email: EmailStr

# Helper Functions

def hash_password(password: str) -> str:
    """Hash a password using SHA256"""
    salt = os.getenv("PASSWORD_SALT", "admin_secret_salt_2026")
    salted_password = password + salt
    return hashlib.sha256(salted_password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against hash"""
    return hash_password(plain_password) == hashed_password


def format_date(dt: datetime) -> str:
    """Format datetime to '21 Nov 2025' format"""
    if dt:
        return dt.strftime("%d %b %Y")
    return None


def create_token(email: str, admin_id: str, name: str) -> str:
    """Create JWT token"""
    payload = {
        "email": email,
        "admin_id": admin_id,
        "name": name,
        "exp": datetime.now() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.now()
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def find_admin_by_email(email: str):
    """Find admin by email (case-insensitive)"""
    # Try exact match first
    admin = admins_collection.find_one({"email": email})
    if admin:
        return admin
    
    # Try lowercase
    admin = admins_collection.find_one({"email": email.lower()})
    if admin:
        return admin
    
    # Try case-insensitive regex
    admin = admins_collection.find_one({
        "email": {"$regex": f"^{email}$", "$options": "i"}
    })
    return admin

# API Endpoints
# @router.get("/")
@app.get("/")
def root():
    """Root endpoint - API information"""
    return {
        "message": "Admin Management API",
        "endpoints": {
            "GET /api/admins": "Get all admins",
            "POST /api/admins": "Add new admin",
            "POST /api/admins/login": "Admin login (returns token)",
            "PATCH /api/admins/block": "Block admin (body: email)",
            "PATCH /api/admins/unblock": "Unblock admin (body: email)",
            "DELETE /api/admins": "Delete admin (body: email)"
        }
    }


@app.get("/api/admins")
def get_all_admins():
    """Get all admins"""
    try:
        admins = list(admins_collection.find({}, {"password": 0}))
        
        result = []
        for admin in admins:
            result.append({
                "name": f"{admin.get('first_name', '')} {admin.get('last_name', '')}".strip(),
                "first_name": admin.get("first_name"),
                "last_name": admin.get("last_name"),
                "email": admin.get("email"),
                "phone": admin.get("phone"),
                "is_blocked": admin.get("is_blocked", False),
                "added_date": format_date(admin.get("created_at")),
                "created_at": admin.get("created_at")
            })
        
        return {
            "total_admins": len(result),
            "admins": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@app.post("/api/admins/add_admin")
def add_admin(admin: AddAdmin):
    """Add new admin"""
    try:
        # Check if email already exists
        existing_admin = find_admin_by_email(admin.email)
        if existing_admin:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        
        # Hash password
        hashed_password = hash_password(admin.password)
        
        # Create admin document
        new_admin = {
            "first_name": admin.first_name,
            "last_name": admin.last_name,
            "email": admin.email.lower(),  # Store in lowercase
            "phone": admin.phone,
            "password": hashed_password,
            "is_blocked": False,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        result = admins_collection.insert_one(new_admin)
        
        return {
            "success": True,
            "message": "Admin added successfully",
            "admin": {
                "id": str(result.inserted_id),
                "name": f"{admin.first_name} {admin.last_name}",
                "email": admin.email.lower(),
                "phone": admin.phone,
                "is_blocked": False,
                "added_date": format_date(datetime.now())
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@app.post("/api/admins/login")
def admin_login(data: AdminLogin):
    """Admin login - Returns JWT token"""
    try:
        # Find admin by email
        admin = find_admin_by_email(data.email)
        
        if not admin:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        # Check if blocked
        if admin.get("is_blocked", False):
            raise HTTPException(
                status_code=403,
                detail="Your account has been blocked. Please contact other admin."
            )
        
        # Verify password
        if not verify_password(data.password, admin["password"]):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
               # "message": "This user is blocked"
                
            )
        
        # Generate JWT token
        admin_id = str(admin.get("_id"))
        name = f"{admin.get('first_name', '')} {admin.get('last_name', '')}".strip()
        token = create_token(admin.get("email"), admin_id, name)
        
        return {
            "success": True,
            "message": "Login successful",
            "token": token,
           # "token_type": "Bearer",
           # "expires_in": JWT_EXPIRATION_HOURS * 3600,
            "admin": {
                "id": admin_id,
                "name": name,
                "email": admin.get("email"),
                "phone": admin.get("phone"),
                "photo": admin.get("photo")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@app.patch("/api/admins/block")
def block_admin(data: AdminEmail):
    """Block an admin"""
    try:
        # Find admin by email
        admin = find_admin_by_email(data.email)
        
        if not admin:
            raise HTTPException(
                status_code=404,
                detail="Admin not found"
            )
        
        # Check if already blocked
        if admin.get("is_blocked", False):
            raise HTTPException(
                status_code=400,
                detail="Admin is already blocked"
            )
        
        # Block admin
        admins_collection.update_one(
            {"_id": admin["_id"]},
            {
                "$set": {
                    "is_blocked": True,
                    "blocked_at": datetime.now(),
                    "updated_at": datetime.now()
                }
            }
        )
        
        return {
            "success": True,
            "message": "Admin blocked successfully",
            "admin": {
                "name": f"{admin.get('first_name', '')} {admin.get('last_name', '')}".strip(),
                "email": admin["email"],
                "is_blocked": True
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@app.patch("/api/admins/unblock")
def unblock_admin(data: AdminEmail):
    """Unblock an admin"""
    try:
        # Find admin by email
        admin = find_admin_by_email(data.email)
        
        if not admin:
            raise HTTPException(
                status_code=404,
                detail="Admin not found"
            )
        
        # Check if already unblocked
        if not admin.get("is_blocked", False):
            raise HTTPException(
                status_code=400,
                detail="Admin is not blocked"
            )
        
        # Unblock admin
        admins_collection.update_one(
            {"_id": admin["_id"]},
            {
                "$set": {
                    "is_blocked": False,
                    "unblocked_at": datetime.now(),
                    "updated_at": datetime.now()
                }
            }
        )
        
        return {
            "success": True,
            "message": "Admin unblocked successfully",
            "admin": {
                "name": f"{admin.get('first_name', '')} {admin.get('last_name', '')}".strip(),
                "email": admin["email"],
                "is_blocked": False
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@app.delete("/api/admins/delete")
def delete_admin(data: AdminEmail):
    """Delete an admin"""
    try:
        # Find admin by email
        admin = find_admin_by_email(data.email)
        
        if not admin:
            raise HTTPException(
                status_code=404,
                detail="Admin not found"
            )
        
        # Delete admin
        admins_collection.delete_one({"_id": admin["_id"]})
        
        return {
            "success": True,
            "message": "Admin deleted successfully",
            "deleted_admin": {
                "name": f"{admin.get('first_name', '')} {admin.get('last_name', '')}".strip(),
                "email": admin["email"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@app.post("/api/admins/reset-password")
def reset_password(data: AdminLogin):
    """
    Reset password for an admin
    Use this to fix password if login doesn't work
    """
    try:
        # Find admin by email
        admin = find_admin_by_email(data.email)
        
        if not admin:
            raise HTTPException(
                status_code=404,
                detail="Admin not found"
            )
        
        # Hash new password
        hashed_password = hash_password(data.password)
        
        # Update password
        admins_collection.update_one(
            {"_id": admin["_id"]},
            {
                "$set": {
                    "password": hashed_password,
                    "updated_at": datetime.now()
                }
            }
        )
        
        return {
            "success": True,
            "message": "Password reset successfully",
            "email": admin["email"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("ADMIN MANAGEMENT API SERVER".center(60))
    print("=" * 60)
    print("\nAPI Endpoints:")
    print("  GET    /api/admins              - Get all admins")
    print("  POST   /api/admins              - Add new admin")
    print("  POST   /api/admins/login        - Admin login (JWT)")
    print("  PATCH  /api/admins/block        - Block admin")
    print("  PATCH  /api/admins/unblock      - Unblock admin")
    print("  DELETE /api/admins              - Delete admin")
    print("  POST   /api/admins/reset-password - Reset password")
    print("=" * 60)
    print("\nServer running at: http://10.10.20.111:8088")
    print("API Documentation: http://10.10.20.111:8088/docs")
    print("=" * 60 + "\n")
    
    uvicorn.run(app, host="10.10.20.111", port=8088, reload=True)