import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
from passlib.context import CryptContext
from bson import ObjectId
from dotenv import load_dotenv

# --- CONFIGURATION ---
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB Connection (Render Environment Variables are prioritized)
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'dancebuddy')

if not MONGO_URL:
    # Fallback only for local development
    MONGO_URL = "mongodb://localhost:27017"

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# SECURITY - Using Argon2 to fix the "72 bytes" bcrypt limit issue
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
SECRET_KEY = os.environ.get("SECRET_KEY", "dancebuddy-super-secret-key-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 1 week

security = HTTPBearer()
app = FastAPI(title="DanceBuddy API", version="2.1")
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    except Exception:
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
    # Check if user exists
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
    
    access_token = create_access_token({"sub": str(result.inserted_id)})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": format_user_response(user_dict)
    }

@api_router.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email.lower()})
    
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token({"sub": str(user["_id"])})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": format_user_response(user)
    }

# --- PUBLIC ROUTES ---
@api_router.get("/health")
async def health():
    return {"status": "ok", "version": "2.1", "db": "connected" if MONGO_URL else "local"}

@api_router.get("/public/cities")
async def get_cities():
    cities = ["Istanbul", "Izmir", "Berlin", "London", "Paris", "New York", "Madrid"]
    return {"cities": cities}

# --- APP SETUP ---
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
