import os
import sys
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr
from jose import jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

# --- RENDER LOG OPTIMIZATION ---
# Forces logs to flush instantly so you can see them on the Render dashboard
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# --- CONFIGURATION ---
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Connection logic: No more localhost fallback. If MONGO_URL is missing, it will warn you.
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'dancebuddy')

if not MONGO_URL:
    print("❌ CRITICAL ERROR: MONGO_URL environment variable is missing!", flush=True)
    # Falling back to localhost only for local dev safety, but this will fail on Render
    MONGO_URL = "mongodb://localhost:27017"
else:
    print(f"✅ Database Connection Initialized: {DB_NAME}", flush=True)

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# SECURITY - Locked to argon2 to prevent login issues with old bcrypt data
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
SECRET_KEY = os.environ.get("SECRET_KEY", "dancebuddy-super-secret-key-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 

security = HTTPBearer()
app = FastAPI(title="DanceBuddy API", version="2.5")
api_router = APIRouter(prefix="/api")

# --- LOGGING MIDDLEWARE ---
# This is what makes every phone request visible in Render logs
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()
        print(f"📥 REQUEST: {request.method} {request.url.path}", flush=True)
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        print(f"📤 RESPONSE: {request.method} {request.url.path} - Status: {response.status_code} ({duration:.2f}s)", flush=True)
        return response

app.add_middleware(LoggingMiddleware)

# --- MODELS ---
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    city: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    city: str
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# --- HELPERS ---
def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        print(f"❌ Verification Error: {e}", flush=True)
        return False

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def format_user_response(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "city": user.get("city", ""),
        "created_at": user.get("created_at", datetime.utcnow()),
    }

# --- AUTH ROUTES ---
@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserRegister):
    print(f"📝 Attempting to register: {user_data.email}", flush=True)
    if await db.users.find_one({"email": user_data.email.lower()}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_dict = {
        "name": user_data.name,
        "email": user_data.email.lower(),
        "password_hash": get_password_hash(user_data.password),
        "city": user_data.city,
        "created_at": datetime.utcnow()
    }
    
    result = await db.users.insert_one(user_dict)
    user_dict["_id"] = result.inserted_id
    print(f"✅ User created in database: {user_data.email}", flush=True)
    
    access_token = create_access_token({"sub": str(result.inserted_id)})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": format_user_response(user_dict)
    }

@api_router.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    print(f"🔑 Login attempt for: {credentials.email}", flush=True)
    user = await db.users.find_one({"email": credentials.email.lower()})
    
    if not user or not verify_password(credentials.password, user["password_hash"]):
        print(f"❌ Invalid credentials for: {credentials.email}", flush=True)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    print(f"🔓 Successful login: {credentials.email}", flush=True)
    access_token = create_access_token({"sub": str(user["_id"])})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": format_user_response(user)
    }

@api_router.get("/health")
async def health():
    return {"status": "ok", "db": DB_NAME, "connected": True}

# --- APP SETUP ---
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print(f"🚀 API STARTUP SUCCESSFUL | Database: {DB_NAME}", flush=True)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
