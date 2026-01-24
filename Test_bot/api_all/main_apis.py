from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os

# Create uploads folder
os.makedirs("uploads/profile_photos", exist_ok=True)

# Import your existing API apps

from admin_api import app as admin_app
from login_forgetPass import app as auth_app
from profile_api import app as profile_app
from test_api_final_2 import app as conversation_app
from telegram_chat_api import app as telegram_app
#from api_starterbot import app as starterbot_app

# Create Main App

app = FastAPI(
    title="Combined API Server",
    description="All APIs running on one server",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
try:
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
except:
    pass

# Mount all your existing apps

# Each app is mounted at its own path prefix
app.mount("/admin", admin_app)        # /admin/api/admins/...
app.mount("/auth", auth_app)          # /auth/api/...
app.mount("/profile", profile_app)    # /profile/api/profile/...
app.mount("/conv", conversation_app)  # /conv/api/...
app.mount("/telegram", telegram_app)  # /telegram/api/...
#app.mount("/starter", starterbot_app) # /starter/...

# Root Endpoint

@app.get("/")
def root():
    return {
        "message": "Hello, Welcome to our server!",
       
    }

# Run Server

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("COMBINED API SERVER".center(70))
    print("=" * 70)
    print("\n📦 Your API files are imported and running together:")
    print("   • admin_api.py        → /admin/*")
    print("   • login_forgetPass.py → /auth/*")
    print("   • profile_api.py      → /profile/*")
    print("   • test_api_final_2.py → /conv/*")
    print("   • telegram_chat_api.py→ /telegram/*")
   # print("   • api_starterbot.py   → /starter/*")
    print("\n📚 API Documentation:")
    print("   http://10.10.20.111:8080/admin/docs")
    print("   http://10.10.20.111:8080/auth/docs")
    print("   http://10.10.20.111:8080/profile/docs")
    print("   http://10.10.20.111:8080/conv/docs")
    print("   http://10.10.20.111:8080/telegram/docs")
   # print("   http://10.10.20.111:8080/starter/docs")
    print("\n" + "=" * 70)
    print(f"🌐 Server running at: http://10.10.20.111:8080")
    print("=" * 70 + "\n")
    
    uvicorn.run(app, host="10.10.20.111", port=8080, reload=True)