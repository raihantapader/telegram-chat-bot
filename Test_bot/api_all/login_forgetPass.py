# auth_api.py
# Authentication API with Login, Forgot Password, OTP, and Password Reset
# Default user credentials are in .env file (not visible in code)

import os
import random
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from click import confirm
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv
import uvicorn

load_dotenv()

# MongoDB connection
MongoDB_Url = os.getenv("DB_URI")
client = MongoClient(MongoDB_Url)
db = client['Raihan']
users_collection = db['users']
otp_collection = db['otp_codes']

# Email Configuration (Gmail SMTP)
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# FastAPI app
app = FastAPI(title="Authentication API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models

# class UserRegister(BaseModel):
#     email: EmailStr
#     password: str
#     name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ForgotPassword(BaseModel):
    email: EmailStr


class VerifyOTP(BaseModel):
    email: EmailStr
    otp: str


class ResetPassword(BaseModel):
   # email: EmailStr
    otp: str
    new_password: str
    confirm_password: str


class ChangePassword(BaseModel):
    email: EmailStr
    old_password: str
    new_password: str

# Helper Functions

def hash_password(password: str) -> str:
    """Hash a password using SHA256 with salt"""
    salt = os.getenv("PASSWORD_SALT", "default_secret_salt_2026")
    salted_password = password + salt
    return hashlib.sha256(salted_password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against hash"""
    return hash_password(plain_password) == hashed_password


def generate_otp() -> str:
    """Generate 6-digit OTP"""
    return str(random.randint(100000, 999999))


def send_otp_email(to_email: str, otp: str) -> bool:
    """Send OTP via email"""
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print(f"⚠️ Email not configured. OTP for {to_email}: {otp}")
        return True
    
    try:
        message = MIMEMultipart()
        message["From"] = EMAIL_ADDRESS
        message["To"] = to_email
        message["Subject"] = "Password Reset OTP"
        
        body = f"""
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>Your OTP code is:</p>
            <h1 style="color: #4CAF50; font-size: 36px;">{otp}</h1>
            <p>This code will expire in <strong>10 minutes</strong>.</p>
            <p>If you didn't request this, please ignore this email.</p>
        </body>
        </html>
        """
        
        message.attach(MIMEText(body, "html"))
        
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, to_email, message.as_string())
        
        return True
    except Exception as e:
        print(f"Email Error: {e}")
        print(f"⚠️ OTP for {to_email}: {otp}")
        return True


def create_default_user():
    """Create default admin user from .env if not exists"""
    default_email = os.getenv("DEFAULT_ADMIN_EMAIL")
    default_password = os.getenv("DEFAULT_ADMIN_PASSWORD")
    default_name = os.getenv("DEFAULT_ADMIN_NAME", "Admin")
    
    # Skip if no default credentials in .env
    if not default_email or not default_password:
        print("ℹ️ No default admin credentials in .env - skipping")
        return
    
    # Check if already exists
    existing_user = users_collection.find_one({"email": default_email})
    
    if not existing_user:
        hashed_password = hash_password(default_password)
        
        default_user = {
            "email": default_email,
            "password": hashed_password,
            "name": default_name,
            "is_admin": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        users_collection.insert_one(default_user)
        print(f"✅ Default admin user created")
    else:
        print(f"✅ Default admin user exists")

# API Endpoints

@app.get("/")
def root():
    """Root endpoint - API information"""
    return {
        "message": "Authentication API",
        "endpoints": {
            "POST /api/register": "Register new user",
            "POST /api/login": "Login user",
            "POST /api/forgot-password": "Send OTP to email",
            "POST /api/verify-otp": "Verify OTP code",
            "POST /api/reset-password": "Reset password with OTP",
            "POST /api/change-password": "Change password (when logged in)",
            "GET /api/users": "Get all users"
        }
    }


# @app.post("/api/register")
# def register_user(user: UserRegister):
#     """Register a new user"""
#     try:
#         existing_user = users_collection.find_one({"email": user.email})
#         if existing_user:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Email already registered"
#             )
        
#         hashed_password = hash_password(user.password)
        
#         new_user = {
#             "email": user.email,
#             "password": hashed_password,
#             "name": user.name,
#             "is_admin": False,
#             "created_at": datetime.now(),
#             "updated_at": datetime.now()
#         }
        
#         users_collection.insert_one(new_user)
        
#         return {
#             "success": True,
#             "message": "User registered successfully",
#             "user": {
#                 "email": user.email,
#                 "name": user.name
#             }
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error: {e}")


@app.post("/api/login")
def login_user(user: UserLogin):
    """Login user with email and password"""
    try:
        db_user = users_collection.find_one({"email": user.email})
        
        if not db_user:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        if not verify_password(user.password, db_user["password"]):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        return {
            "success": True,
            "message": "Login successful",
            "user": {
                "email": db_user["email"],
                "name": db_user["name"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@app.post("/api/forgot-password")
def forgot_password(data: ForgotPassword):
    """Send OTP to user's email for password reset"""
    try:
        db_user = users_collection.find_one({"email": data.email})
        
        if not db_user:
            raise HTTPException(
                status_code=404,
                detail="Email not found"
            )
        
        otp = generate_otp()
        
        otp_data = {
            "email": data.email,
            "otp": otp,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(minutes=10),
            "used": False
        }
        
        otp_collection.delete_many({"email": data.email})
        otp_collection.insert_one(otp_data)
        
        send_otp_email(data.email, otp)
        
        return {
            "success": True,
            "message": "OTP sent to your email",
            "email": data.email,
            "otp_for_testing": otp  # Remove this in production!
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@app.post("/api/verify-otp")
def verify_otp(data: VerifyOTP):
    """Verify OTP code"""
    try:
        otp_record = otp_collection.find_one({
            "email": data.email,
            "otp": data.otp,
            "used": False
        })
        
        if not otp_record:
            raise HTTPException(
                status_code=400,
                detail="Invalid OTP"
            )
        
        if datetime.now() > otp_record["expires_at"]:
            raise HTTPException(
                status_code=400,
                detail="OTP expired. Please request a new one."
            )
        
        return {
            "success": True,
            "message": "OTP verified successfully. You can now reset your password.",
            "email": data.email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@app.post("/api/reset-password")
def reset_password(data: ResetPassword):
    """Reset password with OTP verification"""
    try:
        # Check if passwords match
        if data.new_password != data.confirm_password:
            raise HTTPException(
                status_code=400,
                detail="Passwords do not match"
            )
        
        # Find OTP record (get email from OTP)
        otp_record = otp_collection.find_one({
            "otp": data.otp,
            "used": False
        })
        
        if not otp_record:
            raise HTTPException(
                status_code=400,
                detail="Invalid OTP"
            )
        
        if datetime.now() > otp_record["expires_at"]:
            raise HTTPException(
                status_code=400,
                detail="OTP expired. Please request a new one."
            )
        
        # Get email from OTP record
        email = otp_record["email"]
        
        # Hash new password
        hashed_password = hash_password(data.new_password)
        
        # Update user's password
        result = users_collection.update_one(
            {"email": email},
            {
                "$set": {
                    "password": hashed_password,
                    "updated_at": datetime.now()
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        
        # Mark OTP as used
        otp_collection.update_one(
            {"_id": otp_record["_id"]},
            {"$set": {"used": True}}
        )
        
        return {
            "success": True,
            "message": "Password reset successful. You can now login with your new password."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@app.post("/api/change-password")
def change_password(data: ChangePassword):
    """Change password when user knows old password"""
    try:
        db_user = users_collection.find_one({"email": data.email})
        
        if not db_user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        
        if not verify_password(data.old_password, db_user["password"]):
            raise HTTPException(
                status_code=401,
                detail="Old password is incorrect"
            )
        
        hashed_password = hash_password(data.new_password)
        
        users_collection.update_one(
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
            "message": "Password changed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@app.get("/api/users")
def get_all_users():
    """Get all registered users"""
    try:
        users = list(users_collection.find({}, {"password": 0}))
        
        result = []
        for user in users:
            result.append({
                "email": user.get("email"),
                "name": user.get("name"),
                "created_at": user.get("created_at"),
                "updated_at": user.get("updated_at")
            })
        
        return {
            "total_users": len(result),
            "users": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@app.delete("/api/users/{email}")
def delete_user(email: str):
    """Delete a user by email"""
    try:
        default_email = os.getenv("DEFAULT_ADMIN_EMAIL")
        if email == default_email:
            raise HTTPException(
                status_code=403,
                detail="Cannot delete default admin user"
            )
        
        result = users_collection.delete_one({"email": email})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        
        otp_collection.delete_many({"email": email})
        
        return {
            "success": True,
            "message": f"User {email} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")

# Startup Event
@app.on_event("startup")
def startup_event():
    """Run on startup"""
    create_default_user()


if __name__ == "__main__":
    print("=" * 60)
    print("AUTHENTICATION API SERVER".center(60))
    print("=" * 60)
    print("\nAPI Endpoints:")
    print("  POST   /api/register        - Register new user")
    print("  POST   /api/login           - Login user")
    print("  POST   /api/forgot-password - Send OTP to email")
    print("  POST   /api/verify-otp      - Verify OTP code")
    print("  POST   /api/reset-password  - Reset password with OTP")
    print("  POST   /api/change-password - Change password")
    print("  GET    /api/users           - Get all users")
    print("  DELETE /api/users/{email}   - Delete a user")
    print("=" * 60)
    print("\nServer running at: http://10.10.20.111:8087")
    print("API Documentation: http://10.10.20.111:8087/docs")
    print("=" * 60 + "\n")
    
    create_default_user()
    
    uvicorn.run(app, host="10.10.20.111", port=8087, reload=True)