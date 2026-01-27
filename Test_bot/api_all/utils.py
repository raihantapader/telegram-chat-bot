# utils.py
# Shared utility functions for all APIs

import os
import hashlib
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


def hash_password(password: str) -> str:
    """Hash a password using SHA256 with salt"""
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


def format_duration(seconds: float) -> str:
    """Format seconds into readable duration like '1 min 56 sec' or '2 hr 30 min'"""
    if seconds is None:
        return "N/A"
    
    seconds = int(seconds)
    
    if seconds < 60:
        return f"{seconds} sec"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        if secs > 0:
            return f"{minutes} min {secs} sec"
        return f"{minutes} min"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if minutes > 0:
            return f"{hours} hr {minutes} min"
        return f"{hours} hr"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        if hours > 0:
            return f"{days} day {hours} hr"
        return f"{days} day"


def calculate_avg_response_time(messages: list) -> Optional[float]:
    """Calculate average response time in seconds between different roles"""
    if len(messages) < 2:
        return None
    
    response_times = []
    
    for i in range(1, len(messages)):
        prev_msg = messages[i - 1]
        curr_msg = messages[i]
        
        # Only calculate when role changes (sender → receiver or vice versa)
        if prev_msg.get("role") != curr_msg.get("role"):
            prev_time = prev_msg.get("timestamp")
            curr_time = curr_msg.get("timestamp")
            
            if prev_time and curr_time:
                diff = (curr_time - prev_time).total_seconds()
                # Only count reasonable response times (less than 24 hours)
                if 0 < diff < 86400:
                    response_times.append(diff)
    
    if response_times:
        return sum(response_times) / len(response_times)
    return None