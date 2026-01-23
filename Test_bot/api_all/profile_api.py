# profile_api.py
# Profile API - Edit Profile, Upload Photo, Change Password

import os
import hashlib
import base64
import uuid
from datetime import datetime
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pymongo import MongoClient
from pydantic import BaseModel, EmailStr
from typing import Optional
from dotenv import load_dotenv
import uvicorn

load_dotenv()

# MongoDB connection
MongoDB_Url = os.getenv("DB_URI")
client = MongoClient(MongoDB_Url)
db = client['Raihan']
admins_collection = db['admins']

# Create uploads folder for profile photos
UPLOAD_DIR = "uploads/profile_photos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# FastAPI app
app = FastAPI(title="Profile API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (profile photos)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Pydantic Models

class GetProfile(BaseModel):
    email: EmailStr


class UpdateProfile(BaseModel):
    email: EmailStr  # Current email to identify user
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    new_email: Optional[EmailStr] = None
    phone: Optional[str] = None


class ChangePassword(BaseModel):
    email: EmailStr
    current_password: str
    new_password: str
    confirm_password: str


class UpdatePhoto(BaseModel):
    email: EmailStr
    photo_base64: str  # Base64 encoded image

# Helper Functions

def hash_password(password: str) -> str:
    """Hash a password using SHA256"""
    salt = os.getenv("PASSWORD_SALT", "admin_secret_salt_2026")
    salted_password = password + salt
    return hashlib.sha256(salted_password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against hash"""
    return hash_password(plain_password) == hashed_password


def save_photo_from_base64(base64_string: str, email: str) -> str:
    """Save base64 image and return file path"""
    try:
        # Remove data URL prefix if present
        if "," in base64_string:
            base64_string = base64_string.split(",")[1]
        
        # Decode base64
        image_data = base64.b64decode(base64_string)
        
        # Generate unique filename
        filename = f"{email.replace('@', '_').replace('.', '_')}_{uuid.uuid4().hex[:8]}.png"
        filepath = os.path.join(UPLOAD_DIR, filename)
        
        # Save image
        with open(filepath, "wb") as f:
            f.write(image_data)
        
        return f"/uploads/profile_photos/{filename}"
    except Exception as e:
        print(f"Photo save error: {e}")
        return None

# API Endpoints

@app.get("/")
def root():
    """Root endpoint - API information"""
    return {
        "message": "Profile API",
        "endpoints": {
            "POST /api/profile": "Get profile by email",
            "PUT /api/profile": "Update profile",
            "PUT /api/profile/photo": "Update profile photo",
            "PUT /api/profile/password": "Change password"
        }
    }


@app.post("/api/profile")
def get_profile(data: GetProfile):
    """Get admin profile by email"""
    try:
        admin = admins_collection.find_one(
            {"email": data.email},
            {"password": 0}  # Exclude password
        )
        
        if not admin:
            raise HTTPException(
                status_code=404,
                detail="Profile not found"
            )
        
        return {
            "success": True,
            "profile": {
                "first_name": admin.get("first_name", ""),
                "last_name": admin.get("last_name", ""),
                "name": f"{admin.get('first_name', '')} {admin.get('last_name', '')}".strip(),
                "email": admin.get("email"),
                "phone": admin.get("phone", ""),
                "photo": admin.get("photo", None),
                "created_at": admin.get("created_at"),
                "updated_at": admin.get("updated_at")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@app.put("/api/profile")
def update_profile(data: UpdateProfile):
    """
    Update admin profile
    - First Name
    - Last Name
    - Email
    - Phone
    """
    try:
        # Find admin by email
        admin = admins_collection.find_one({"email": data.email})
        
        if not admin:
            raise HTTPException(
                status_code=404,
                detail="Profile not found"
            )
        
        # Build update document
        update_data = {"updated_at": datetime.now()}
        
        if data.first_name:
            update_data["first_name"] = data.first_name
        if data.last_name:
            update_data["last_name"] = data.last_name
        if data.phone:
            update_data["phone"] = data.phone
        
        # Handle email change
        if data.new_email and data.new_email != data.email:
            # Check if new email already exists
            existing = admins_collection.find_one({"email": data.new_email})
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail="Email already in use"
                )
            update_data["email"] = data.new_email
        
        # Update admin
        admins_collection.update_one(
            {"email": data.email},
            {"$set": update_data}
        )
        
        # Get updated profile
        updated_email = data.new_email if data.new_email else data.email
        updated_admin = admins_collection.find_one(
            {"email": updated_email},
            {"password": 0}
        )
        
        return {
            "success": True,
            "message": "Profile updated successfully",
            "profile": {
                "first_name": updated_admin.get("first_name", ""),
                "last_name": updated_admin.get("last_name", ""),
                "name": f"{updated_admin.get('first_name', '')} {updated_admin.get('last_name', '')}".strip(),
                "email": updated_admin.get("email"),
                "phone": updated_admin.get("phone", ""),
                "photo": updated_admin.get("photo", None)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@app.put("/api/profile/photo")
def update_profile_photo(data: UpdatePhoto):
    """
    Update profile photo
    - Accepts base64 encoded image
    """
    try:
        # Find admin by email
        admin = admins_collection.find_one({"email": data.email})
        
        if not admin:
            raise HTTPException(
                status_code=404,
                detail="Profile not found"
            )
        
        # Delete old photo if exists
        old_photo = admin.get("photo")
        if old_photo:
            old_path = old_photo.lstrip("/")
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except:
                    pass
        
        # Save new photo
        photo_path = save_photo_from_base64(data.photo_base64, data.email)
        
        if not photo_path:
            raise HTTPException(
                status_code=400,
                detail="Failed to save photo"
            )
        
        # Update admin with new photo
        admins_collection.update_one(
            {"email": data.email},
            {
                "$set": {
                    "photo": photo_path,
                    "updated_at": datetime.now()
                }
            }
        )
        
        return {
            "success": True,
            "message": "Profile photo updated successfully",
            "photo": photo_path
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@app.post("/api/profile/photo/upload")
async def upload_profile_photo(
    email: str = Form(...),
    photo: UploadFile = File(...)
):
    """
    Upload profile photo (multipart form)
    - Accepts file upload
    """
    try:
        # Find admin by email
        admin = admins_collection.find_one({"email": email})
        
        if not admin:
            raise HTTPException(
                status_code=404,
                detail="Profile not found"
            )
        
        # Delete old photo if exists
        old_photo = admin.get("photo")
        if old_photo:
            old_path = old_photo.lstrip("/")
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except:
                    pass
        
        # Generate unique filename
        ext = photo.filename.split(".")[-1] if "." in photo.filename else "png"
        filename = f"{email.replace('@', '_').replace('.', '_')}_{uuid.uuid4().hex[:8]}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        
        # Save uploaded file
        contents = await photo.read()
        with open(filepath, "wb") as f:
            f.write(contents)
        
        photo_path = f"/uploads/profile_photos/{filename}"
        
        # Update admin with new photo
        admins_collection.update_one(
            {"email": email},
            {
                "$set": {
                    "photo": photo_path,
                    "updated_at": datetime.now()
                }
            }
        )
        
        return {
            "success": True,
            "message": "Profile photo uploaded successfully",
            "photo": photo_path
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@app.put("/api/profile/password")
def change_password(data: ChangePassword):
    """
    Change password
    - Current Password
    - New Password
    - Confirm Password
    """
    try:
        # Find admin by email
        admin = admins_collection.find_one({"email": data.email})
        
        if not admin:
            raise HTTPException(
                status_code=404,
                detail="Profile not found"
            )
        
        # Verify current password
        if not verify_password(data.current_password, admin["password"]):
            raise HTTPException(
                status_code=401,
                detail="Current password is incorrect"
            )
        
        # Check if new passwords match
        if data.new_password != data.confirm_password:
            raise HTTPException(
                status_code=400,
                detail="New password and confirm password do not match"
            )
        
        # Check if new password is same as current
        if data.current_password == data.new_password:
            raise HTTPException(
                status_code=400,
                detail="New password must be different from current password"
            )
        
        # Hash new password
        hashed_password = hash_password(data.new_password)
        
        # Update password
        admins_collection.update_one(
            {"email": data.email},
            {
                "$set": {
                    "password": hashed_password,
                    "updated_at": datetime.now()
                }
            }
        )
        
        return {
            "success": True,
            "message": "Password updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("PROFILE API SERVER".center(60))
    print("=" * 60)
    print("\nAPI Endpoints:")
    print("  POST /api/profile              - Get profile")
    print("  PUT  /api/profile              - Update profile")
    print("  PUT  /api/profile/photo        - Update photo (base64)")
    print("  POST /api/profile/photo/upload - Upload photo (file)")
    print("  PUT  /api/profile/password     - Change password")
    print("=" * 60)
    print("\nServer running at: http://10.10.20.111:8089")
    print("API Documentation: http://10.10.20.111:8089/docs")
    print("=" * 60 + "\n")
    
    uvicorn.run(app, host="10.10.20.111", port=8089, reload=True)