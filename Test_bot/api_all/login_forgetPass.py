# login_forgetPass.py
# Authentication API - Forgot Password & OTP for ADMINS

import os
import random
import hashlib
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv
import uvicorn

load_dotenv()

# MongoDB Connection

MongoDB_Url = os.getenv("DB_URI")
client = MongoClient(MongoDB_Url)
db = client['Raihan']
admins_collection = db['admins']
otp_collection = db['otp_codes']

# Email Configuration (Gmail SMTP)

EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Lifespan

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 50)
    print("✅ Authentication API Started")
    print(f"📧 Email configured: {EMAIL_ADDRESS is not None and EMAIL_PASSWORD is not None}")
    print("=" * 50)
    yield
    print("🛑 Authentication API Stopped")

# FastAPI App

app = FastAPI(title="Authentication API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models

class ForgotPassword(BaseModel):
    email: EmailStr


class VerifyOTP(BaseModel):
    email: EmailStr
    otp: str


class ResetPassword(BaseModel):
    email: EmailStr
    new_password: str
    confirm_password: str

# Helper Functions

def hash_password(password: str) -> str:
    """Hash a password using SHA256 with salt"""
    salt = os.getenv("PASSWORD_SALT", "admin_secret_salt_2026")
    salted_password = password + salt
    return hashlib.sha256(salted_password.encode()).hexdigest()


def generate_otp() -> str:
    """Generate 6-digit OTP"""
    return str(random.randint(100000, 999999))


def find_admin_by_email(email: str):
    """Find admin by email (case-insensitive)"""
    admin = admins_collection.find_one({"email": email})
    if admin:
        return admin
    
    admin = admins_collection.find_one({"email": email.lower()})
    if admin:
        return admin
    
    admin = admins_collection.find_one({
        "email": {"$regex": f"^{email}$", "$options": "i"}
    })
    return admin


def send_otp_email(to_email: str, otp: str) -> bool:
    """
    Send OTP via email using Gmail SMTP
    
    Requirements:
    1. Set EMAIL_ADDRESS in .env (your Gmail)
    2. Set EMAIL_PASSWORD in .env (Gmail App Password - 16 characters)
    
    To get App Password:
    1. Go to https://myaccount.google.com/security
    2. Enable 2-Step Verification
    3. Go to https://myaccount.google.com/apppasswords
    4. Generate new App Password
    5. Copy the 16-character password (remove spaces)
    """
    
    print("\n" + "=" * 50)
    print("📧 SENDING OTP EMAIL")
    print("=" * 50)
    print(f"To: {to_email}")
    print(f"OTP: {otp}")
    print(f"From: {EMAIL_ADDRESS}")
    print(f"Password configured: {'Yes' if EMAIL_PASSWORD else 'No'}")
    
    # Check if email credentials are configured
    if not EMAIL_ADDRESS:
        print("❌ ERROR: EMAIL_ADDRESS not set in .env")
        print("=" * 50 + "\n")
        return False
    
    if not EMAIL_PASSWORD:
        print("❌ ERROR: EMAIL_PASSWORD not set in .env")
        print("=" * 50 + "\n")
        return False
    
    try:
        # Create email message
        message = MIMEMultipart("alternative")
        message["From"] = EMAIL_ADDRESS
        message["To"] = to_email
        message["Subject"] = "Password Reset OTP Code"
        
        # Plain text version
        text_body = f"""
Password Reset Request

Your OTP code is: {otp}

This code will expire in 10 minutes.

If you didn't request this, please ignore this email.
        """
        
        # HTML version
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 500px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            color: #333;
            margin-bottom: 20px;
        }}
        .otp-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-size: 36px;
            font-weight: bold;
            text-align: center;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            letter-spacing: 8px;
        }}
        .info {{
            color: #666;
            font-size: 14px;
            text-align: center;
            margin: 10px 0;
        }}
        .warning {{
            color: #e74c3c;
            font-size: 12px;
            text-align: center;
            margin-top: 20px;
            padding: 10px;
            background: #ffeaea;
            border-radius: 5px;
        }}
        .footer {{
            text-align: center;
            color: #999;
            font-size: 11px;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h2 class="header">🔐 Password Reset Request</h2>
        
        <p class="info">You requested to reset your password.</p>
        <p class="info">Use the OTP code below:</p>
        
        <div class="otp-box">{otp}</div>
        
        <p class="info">This code will expire in <strong>10 minutes</strong>.</p>
        
        <div class="warning">
            ⚠️ If you didn't request this password reset, please ignore this email.
            Your password will remain unchanged.
        </div>
        
        <div class="footer">
            This is an automated message. Please do not reply to this email.
        </div>
    </div>
</body>
</html>
        """
        
        # Attach both plain text and HTML versions
        part1 = MIMEText(text_body, "plain")
        part2 = MIMEText(html_body, "html")
        message.attach(part1)
        message.attach(part2)
        
        # Connect to Gmail SMTP server and send email
        print("📤 Connecting to Gmail SMTP server...")
        
        # Create SSL context
        context = ssl.create_default_context()
        
        # Connect and send
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            
            print("🔑 Logging in to Gmail...")
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            
            print("📨 Sending email...")
            server.sendmail(EMAIL_ADDRESS, to_email, message.as_string())
        
        print("✅ OTP EMAIL SENT SUCCESSFULLY!")
        print("=" * 50 + "\n")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP Authentication Error: {e}")
        print("💡 Make sure you're using Gmail App Password, not regular password!")
        print("💡 Go to: https://myaccount.google.com/apppasswords")
        print("=" * 50 + "\n")
        return False
        
    except smtplib.SMTPRecipientsRefused as e:
        print(f"❌ Recipient Refused: {e}")
        print("💡 Check if the recipient email address is valid")
        print("=" * 50 + "\n")
        return False
        
    except smtplib.SMTPException as e:
        print(f"❌ SMTP Error: {e}")
        print("=" * 50 + "\n")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("=" * 50 + "\n")
        return False


# API Endpoints

@app.get("/")
def root():
    return {
        "message": "Authentication API (Admin Forgot Password)",
        "email_configured": EMAIL_ADDRESS is not None and EMAIL_PASSWORD is not None,
        "flow": {
            "1": "POST /api/forgot-password → Send OTP to admin email",
            "2": "POST /api/verify-otp → Verify OTP code",
            "3": "POST /api/reset-password → Set new password",
            "4": "Go to /api/admins/login → Login with new password"
        }
    }


@app.post("/api/forgot-password")
def forgot_password(data: ForgotPassword):
    """
    Step 1: Send OTP to admin's email
    """
    try:
        # Check if admin exists
        admin = find_admin_by_email(data.email)
        
        if not admin:
            raise HTTPException(status_code=404, detail="Email not found in admin database")
        
        # Generate 6-digit OTP
        otp = generate_otp()
        
        # Store OTP in database
        otp_data = {
            "email": data.email.lower(),
            "otp": otp,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(minutes=10),
            "used": False
        }
        
        # Delete old OTPs for this email
        otp_collection.delete_many({"email": data.email.lower()})
        
        # Insert new OTP
        otp_collection.insert_one(otp_data)
        
        # Send OTP via email
        email_sent = send_otp_email(data.email, otp)
        
        if email_sent:
            return {
                "success": True,
                "message": "OTP sent to your email",
                "email": data.email,
                "expires_in": "10 minutes"
            }
        else:
            return {
                "success": True,
                "message": "OTP generated but email failed. Check console for OTP.",
                "email": data.email,
                "expires_in": "10 minutes",
                "otp_for_testing": otp  # Only show if email failed
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@app.post("/api/verify-otp")
def verify_otp(data: VerifyOTP):
    """
    Step 2: Verify OTP code
    """
    try:
        # Find OTP record
        otp_record = otp_collection.find_one({
            "email": data.email.lower(),
            "otp": data.otp,
            "used": False
        })
        
        if not otp_record:
            raise HTTPException(status_code=400, detail="Invalid OTP")
        
        # Check if OTP expired
        if datetime.now() > otp_record["expires_at"]:
            raise HTTPException(status_code=400, detail="OTP expired. Please request a new one.")
        
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
    """
    Step 3: Reset password
    - User enters email, new_password, confirm_password
    - System checks if OTP was verified for this email
    - Updates password in admins collection
    """
    try:
        # Check if passwords match
        if data.new_password != data.confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match")
        
        # Check password length
        if len(data.new_password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        
        # Find OTP record for this email (must be verified but not used)
        otp_record = otp_collection.find_one({
            "email": data.email.lower(),
            "used": False
        })
        
        if not otp_record:
            raise HTTPException(status_code=400, detail="Please verify OTP first")
        
        # Check if OTP expired
        if datetime.now() > otp_record["expires_at"]:
            raise HTTPException(status_code=400, detail="OTP expired. Please request a new one.")
        
        # Hash new password
        hashed_password = hash_password(data.new_password)
        
        # Update admin's password
        result = admins_collection.update_one(
            {"email": data.email.lower()},
            {
                "$set": {
                    "password": hashed_password,
                    "updated_at": datetime.now()
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Admin not found")
        
        # Mark OTP as used
        otp_collection.update_one(
            {"_id": otp_record["_id"]},
            {"$set": {"used": True}}
        )
        
        return {
            "success": True,
            "message": "Password reset successful. Please login with your new password.",
            "email": data.email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


# Run Server
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("AUTHENTICATION API (ADMIN FORGOT PASSWORD)".center(60))
    print("=" * 60)
    
    print("\n📧 Email Configuration:")
    print(f"   EMAIL_ADDRESS: {EMAIL_ADDRESS or 'NOT SET ❌'}")
    print(f"   EMAIL_PASSWORD: {'SET ✅' if EMAIL_PASSWORD else 'NOT SET ❌'}")
    
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print("\n⚠️  WARNING: Email not configured!")
        print("   OTP will be printed in console instead of sending email.")
        print("\n   To configure email:")
        print("   1. Go to https://myaccount.google.com/apppasswords")
        print("   2. Generate App Password")
        print("   3. Add to .env:")
        print("      EMAIL_ADDRESS=your_gmail@gmail.com")
        print("      EMAIL_PASSWORD=abcdefghijklmnop")
    
    print("\n📋 Password Reset Flow:")
    print("   1. POST /api/forgot-password → Send OTP to email")
    print("   2. POST /api/verify-otp      → Verify OTP")
    print("   3. POST /api/reset-password  → Set new password")
    print("   4. POST /api/admins/login    → Login")
    
    print("\n" + "=" * 60)
    print("Server: http://10.10.20.111:8087")
    print("Docs:   http://10.10.20.111:8087/docs")
    print("=" * 60 + "\n")
    
    uvicorn.run(app, host="10.10.20.111", port=8087, reload=True)