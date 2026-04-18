import os
import sys
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
from bson import ObjectId

# --- RENDER LOG OPTIMIZATION ---
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# --- CONFIGURATION ---
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'dancebuddy')

if not MONGO_URL:
    print("❌ CRITICAL ERROR: MONGO_URL environment variable is missing!", flush=True)
    MONGO_URL = "mongodb://localhost:27017"
else:
    print(f"✅ Database Connection Initialized: {DB_NAME}", flush=True)

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")
SECRET_KEY = os.environ.get("SECRET_KEY", "dancebuddy-super-secret-key-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

security = HTTPBearer()
app = FastAPI(title="DanceBuddy API", version="3.0")
api_router = APIRouter(prefix="/api")

# ===== FIXED 30 CITIES LIST =====
FIXED_CITIES = [
    "Lyon", "Budapest", "Phoenix", "Berlin", "London", "Warsaw", "Tel Aviv", "Cali",
    "Madrid", "New York", "Milan", "Paris", "Santo Domingo", "Istanbul", "Izmir",
    "Edirne", "Antalya", "Konstanz", "Zurich", "Basel", "Munich", "Hamburg",
    "Cologne", "Toronto", "Amsterdam", "Copenhagen", "Oslo", "Helsinki", "Sofia", "Athens"
]

DANCE_STYLES = ["Salsa", "Bachata", "Tango", "West Coast Swing", "Swing"]
DANCE_LEVELS = ["Beginner", "Intermediate", "Advanced"]
EVENT_TYPES = ["Workshop", "Dance Night", "Social Meetup"]
MEMORY_TYPES = ["Funniest Dance Moment", "Most Unforgettable Dance Moment"]

# --- LOGGING MIDDLEWARE ---
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()
        print(f"📥 {request.method} {request.url.path}", flush=True)
        response = await call_next(request)
        duration = time.time() - start_time
        print(f"📤 {request.method} {request.url.path} - {response.status_code} ({duration:.2f}s)", flush=True)
        return response

app.add_middleware(LoggingMiddleware)

# --- MODELS ---
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    city: str
    bio: Optional[str] = ""
    dance_level: Optional[str] = "Beginner"
    dance_styles: Optional[List[str]] = []

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    photo: Optional[str] = None
    gallery: Optional[List[str]] = None
    city: Optional[str] = None
    dance_level: Optional[str] = None
    favorite_dance_music: Optional[str] = None
    dance_styles: Optional[List[str]] = None

class EventCreate(BaseModel):
    title: str
    event_type: str
    city: str
    description: Optional[str] = ""
    start_time: datetime
    end_time: datetime
    dance_styles: Optional[List[str]] = []

class EventComment(BaseModel):
    comment: str

class PartnerRequestCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    city: str
    dance_style: str
    looking_for_level: Optional[str] = None

class MemoryCreate(BaseModel):
    memory_type: str
    content: str
    city: Optional[str] = None

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

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Authentication failed")

def format_user_response(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "city": user.get("city", ""),
        "bio": user.get("bio", ""),
        "photo": user.get("photo"),
        "gallery": user.get("gallery", []) or [],
        "dance_level": user.get("dance_level", "Beginner"),
        "favorite_dance_music": user.get("favorite_dance_music", ""),
        "dance_styles": user.get("dance_styles", []) or [],
        "created_at": user.get("created_at", datetime.utcnow()),
    }

def format_event_response(event: dict, include_attendees: bool = False, include_comments: bool = False) -> dict:
    result = {
        "id": str(event["_id"]),
        "title": event.get("title", ""),
        "event_type": event.get("event_type", "Dance Night"),
        "city": event.get("city", ""),
        "description": event.get("description", ""),
        "start_time": event.get("start_time"),
        "end_time": event.get("end_time"),
        "dance_styles": event.get("dance_styles", []) or [],
        "created_by": event.get("created_by"),
        "created_at": event.get("created_at"),
        "attendees_count": len(event.get("attendees", []) or []),
    }
    if include_attendees:
        result["attendees"] = event.get("attendees", []) or []
    if include_comments:
        result["comments"] = event.get("comments", []) or []
    return result

# ===== AUTH ROUTES =====
@api_router.post("/auth/register")
async def register(user_data: UserRegister):
    print(f"📝 Registering: {user_data.email}", flush=True)
    if await db.users.find_one({"email": user_data.email.lower()}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_dict = {
        "name": user_data.name,
        "email": user_data.email.lower(),
        "password_hash": get_password_hash(user_data.password),
        "city": user_data.city,
        "bio": user_data.bio or "",
        "photo": None,
        "gallery": [],
        "dance_level": user_data.dance_level or "Beginner",
        "favorite_dance_music": "",
        "dance_styles": user_data.dance_styles or [],
        "created_at": datetime.utcnow()
    }
    
    result = await db.users.insert_one(user_dict)
    user_dict["_id"] = result.inserted_id
    print(f"✅ User created: {user_data.email}", flush=True)
    
    return {
        "access_token": create_access_token({"sub": str(result.inserted_id)}),
        "token_type": "bearer",
        "user": format_user_response(user_dict)
    }

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    print(f"🔑 Login: {credentials.email}", flush=True)
    user = await db.users.find_one({"email": credentials.email.lower()})
    
    if not user or not verify_password(credentials.password, user["password_hash"]):
        print(f"❌ Invalid credentials: {credentials.email}", flush=True)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    print(f"✅ Login success: {credentials.email}", flush=True)
    return {
        "access_token": create_access_token({"sub": str(user["_id"])}),
        "token_type": "bearer",
        "user": format_user_response(user)
    }

# ===== USER ROUTES =====
@api_router.get("/users/me")
async def get_my_profile(current_user=Depends(get_current_user)):
    return format_user_response(current_user)

@api_router.put("/users/me")
async def update_profile(user_data: UserUpdate, current_user=Depends(get_current_user)):
    update_dict = {}
    if user_data.name is not None: update_dict["name"] = user_data.name
    if user_data.bio is not None: update_dict["bio"] = user_data.bio
    if user_data.photo is not None: update_dict["photo"] = user_data.photo
    if user_data.gallery is not None: update_dict["gallery"] = user_data.gallery[:5]
    if user_data.city is not None: update_dict["city"] = user_data.city
    if user_data.dance_level is not None: update_dict["dance_level"] = user_data.dance_level
    if user_data.favorite_dance_music is not None: update_dict["favorite_dance_music"] = user_data.favorite_dance_music
    if user_data.dance_styles is not None: update_dict["dance_styles"] = user_data.dance_styles
    
    if update_dict:
        await db.users.update_one({"_id": current_user["_id"]}, {"$set": update_dict})
    
    updated = await db.users.find_one({"_id": current_user["_id"]})
    return format_user_response(updated)

@api_router.get("/users")
async def get_all_users(city: Optional[str] = None, current_user=Depends(get_current_user)):
    query = {"_id": {"$ne": current_user["_id"]}}
    if city and city in FIXED_CITIES:
        query["city"] = city
    users = await db.users.find(query).limit(100).to_list(100)
    return [format_user_response(u) for u in users]

@api_router.get("/users/{user_id}")
async def get_user_detail(user_id: str, current_user=Depends(get_current_user)):
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return format_user_response(user)
    except:
        raise HTTPException(status_code=400, detail="Invalid user ID")

# ===== PUBLIC ROUTES (Guest Access) =====
@api_router.get("/public/events")
async def get_public_events(city: Optional[str] = None):
    print(f"👀 Guest viewing events", flush=True)
    now = datetime.utcnow()
    query = {"end_time": {"$gt": now}}
    if city and city in FIXED_CITIES:
        query["city"] = city
    events = await db.events.find(query).sort("start_time", 1).limit(50).to_list(50)
    return [format_event_response(e) for e in events]

@api_router.get("/public/cities")
async def get_cities():
    return {"cities": FIXED_CITIES}

@api_router.get("/public/dance-styles")
async def get_dance_styles():
    return {"dance_styles": DANCE_STYLES}

# ===== EVENT ROUTES (Auth Required) =====
@api_router.get("/events")
async def get_events(city: Optional[str] = None, current_user=Depends(get_current_user)):
    now = datetime.utcnow()
    query = {"end_time": {"$gt": now}}
    if city and city in FIXED_CITIES:
        query["city"] = city
    events = await db.events.find(query).sort("start_time", 1).limit(50).to_list(50)
    return [format_event_response(e, include_attendees=True, include_comments=True) for e in events]

@api_router.post("/events")
async def create_event(event_data: EventCreate, current_user=Depends(get_current_user)):
    if event_data.city not in FIXED_CITIES:
        raise HTTPException(status_code=400, detail="Invalid city")
    if event_data.end_time <= event_data.start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")
    
    event = {
        "title": event_data.title,
        "event_type": event_data.event_type,
        "city": event_data.city,
        "description": event_data.description or "",
        "start_time": event_data.start_time,
        "end_time": event_data.end_time,
        "dance_styles": event_data.dance_styles or [],
        "created_by": str(current_user["_id"]),
        "created_at": datetime.utcnow(),
        "attendees": [],
        "comments": []
    }
    result = await db.events.insert_one(event)
    event["_id"] = result.inserted_id
    print(f"✅ Event created: {event_data.title}", flush=True)
    return format_event_response(event, include_attendees=True, include_comments=True)

@api_router.post("/events/{event_id}/join")
async def join_event(event_id: str, current_user=Depends(get_current_user)):
    try:
        event = await db.events.find_one({"_id": ObjectId(event_id)})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        user_id = str(current_user["_id"])
        attendees = event.get("attendees", []) or []
        
        if any(a.get("user_id") == user_id for a in attendees):
            raise HTTPException(status_code=400, detail="Already joined")
        
        attendee_info = {
            "user_id": user_id,
            "name": current_user.get("name", ""),
            "photo": current_user.get("photo"),
            "joined_at": datetime.utcnow()
        }
        await db.events.update_one({"_id": ObjectId(event_id)}, {"$push": {"attendees": attendee_info}})
        print(f"✅ User joined event: {event_id}", flush=True)
        return {"success": True, "message": "Joined event"}
    except HTTPException:
        raise
    except:
        raise HTTPException(status_code=400, detail="Invalid event ID")

@api_router.delete("/events/{event_id}/join")
async def leave_event(event_id: str, current_user=Depends(get_current_user)):
    user_id = str(current_user["_id"])
    await db.events.update_one({"_id": ObjectId(event_id)}, {"$pull": {"attendees": {"user_id": user_id}}})
    return {"success": True, "message": "Left event"}

@api_router.post("/events/{event_id}/comments")
async def add_comment(event_id: str, comment_data: EventComment, current_user=Depends(get_current_user)):
    try:
        event = await db.events.find_one({"_id": ObjectId(event_id)})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        comment = {
            "id": str(ObjectId()),
            "user_id": str(current_user["_id"]),
            "user_name": current_user.get("name", ""),
            "user_photo": current_user.get("photo"),
            "comment": comment_data.comment,
            "created_at": datetime.utcnow()
        }
        await db.events.update_one({"_id": ObjectId(event_id)}, {"$push": {"comments": comment}})
        return comment
    except HTTPException:
        raise
    except:
        raise HTTPException(status_code=400, detail="Invalid event ID")

# ===== PARTNER REQUESTS =====
@api_router.get("/partner-requests")
async def get_partner_requests(city: Optional[str] = None, dance_style: Optional[str] = None, current_user=Depends(get_current_user)):
    query = {}
    if city and city in FIXED_CITIES:
        query["city"] = city
    if dance_style:
        query["dance_style"] = dance_style
    requests = await db.partner_requests.find(query).sort("created_at", -1).limit(50).to_list(50)
    return [{
        "id": str(r["_id"]),
        "title": r.get("title", ""),
        "description": r.get("description", ""),
        "city": r.get("city", ""),
        "dance_style": r.get("dance_style", ""),
        "looking_for_level": r.get("looking_for_level"),
        "user_id": r.get("user_id"),
        "user_name": r.get("user_name", ""),
        "user_photo": r.get("user_photo"),
        "created_at": r.get("created_at")
    } for r in requests]

@api_router.post("/partner-requests")
async def create_partner_request(request_data: PartnerRequestCreate, current_user=Depends(get_current_user)):
    if request_data.city not in FIXED_CITIES:
        raise HTTPException(status_code=400, detail="Invalid city")
    
    partner_request = {
        "title": request_data.title,
        "description": request_data.description or "",
        "city": request_data.city,
        "dance_style": request_data.dance_style,
        "looking_for_level": request_data.looking_for_level,
        "user_id": str(current_user["_id"]),
        "user_name": current_user.get("name", ""),
        "user_photo": current_user.get("photo"),
        "created_at": datetime.utcnow()
    }
    result = await db.partner_requests.insert_one(partner_request)
    partner_request["id"] = str(result.inserted_id)
    print(f"✅ Partner request created: {request_data.title}", flush=True)
    return partner_request

@api_router.delete("/partner-requests/{request_id}")
async def delete_partner_request(request_id: str, current_user=Depends(get_current_user)):
    try:
        request = await db.partner_requests.find_one({"_id": ObjectId(request_id)})
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        if request.get("user_id") != str(current_user["_id"]):
            raise HTTPException(status_code=403, detail="Not authorized")
        await db.partner_requests.delete_one({"_id": ObjectId(request_id)})
        return {"success": True}
    except HTTPException:
        raise
    except:
        raise HTTPException(status_code=400, detail="Invalid request ID")

# ===== DANCE MEMORIES =====
@api_router.get("/memories")
async def get_memories(memory_type: Optional[str] = None, current_user=Depends(get_current_user)):
    query = {}
    if memory_type and memory_type in MEMORY_TYPES:
        query["memory_type"] = memory_type
    memories = await db.memories.find(query).sort("created_at", -1).limit(50).to_list(50)
    return [{
        "id": str(m["_id"]),
        "memory_type": m.get("memory_type", ""),
        "content": m.get("content", ""),
        "city": m.get("city"),
        "user_id": m.get("user_id"),
        "user_name": m.get("user_name", ""),
        "user_photo": m.get("user_photo"),
        "likes": m.get("likes", []) or [],
        "likes_count": len(m.get("likes", []) or []),
        "created_at": m.get("created_at")
    } for m in memories]

@api_router.post("/memories")
async def create_memory(memory_data: MemoryCreate, current_user=Depends(get_current_user)):
    if memory_data.memory_type not in MEMORY_TYPES:
        raise HTTPException(status_code=400, detail="Invalid memory type")
    
    memory = {
        "memory_type": memory_data.memory_type,
        "content": memory_data.content,
        "city": memory_data.city,
        "user_id": str(current_user["_id"]),
        "user_name": current_user.get("name", ""),
        "user_photo": current_user.get("photo"),
        "likes": [],
        "created_at": datetime.utcnow()
    }
    result = await db.memories.insert_one(memory)
    memory["id"] = str(result.inserted_id)
    memory["likes_count"] = 0
    print(f"✅ Memory created", flush=True)
    return memory

@api_router.post("/memories/{memory_id}/like")
async def like_memory(memory_id: str, current_user=Depends(get_current_user)):
    try:
        user_id = str(current_user["_id"])
        memory = await db.memories.find_one({"_id": ObjectId(memory_id)})
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        likes = memory.get("likes", []) or []
        if user_id in likes:
            await db.memories.update_one({"_id": ObjectId(memory_id)}, {"$pull": {"likes": user_id}})
            return {"liked": False, "likes_count": len(likes) - 1}
        else:
            await db.memories.update_one({"_id": ObjectId(memory_id)}, {"$push": {"likes": user_id}})
            return {"liked": True, "likes_count": len(likes) + 1}
    except HTTPException:
        raise
    except:
        raise HTTPException(status_code=400, detail="Invalid memory ID")

@api_router.delete("/memories/{memory_id}")
async def delete_memory(memory_id: str, current_user=Depends(get_current_user)):
    try:
        memory = await db.memories.find_one({"_id": ObjectId(memory_id)})
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        if memory.get("user_id") != str(current_user["_id"]):
            raise HTTPException(status_code=403, detail="Not authorized")
        await db.memories.delete_one({"_id": ObjectId(memory_id)})
        return {"success": True}
    except HTTPException:
        raise
    except:
        raise HTTPException(status_code=400, detail="Invalid memory ID")

# ===== SEED DATA =====
@api_router.post("/seed")
async def seed_database():
    user_count = await db.users.count_documents({})
    if user_count > 5:
        return {"message": "Already seeded", "users": user_count}
    
    dummy_users = [
        {"name": "Maria Salsa", "email": "maria@example.com", "password_hash": get_password_hash("test123"), "city": "Istanbul", "bio": "Salsa dancer", "dance_level": "Advanced", "dance_styles": ["Salsa"], "created_at": datetime.utcnow()},
        {"name": "Jean WCS", "email": "jean@example.com", "password_hash": get_password_hash("test123"), "city": "Lyon", "bio": "WCS enthusiast", "dance_level": "Intermediate", "dance_styles": ["West Coast Swing"], "created_at": datetime.utcnow()},
        {"name": "Klaus Tango", "email": "klaus@example.com", "password_hash": get_password_hash("test123"), "city": "Berlin", "bio": "Tango dancer", "dance_level": "Advanced", "dance_styles": ["Tango"], "created_at": datetime.utcnow()},
        {"name": "Sarah Bachata", "email": "sarah@example.com", "password_hash": get_password_hash("test123"), "city": "New York", "bio": "Bachata teacher", "dance_level": "Advanced", "dance_styles": ["Bachata"], "created_at": datetime.utcnow()},
        {"name": "Peter Swing", "email": "peter@example.com", "password_hash": get_password_hash("test123"), "city": "Budapest", "bio": "Swing dancer", "dance_level": "Beginner", "dance_styles": ["Swing"], "created_at": datetime.utcnow()},
    ]
    
    for user in dummy_users:
        if not await db.users.find_one({"email": user["email"]}):
            await db.users.insert_one(user)
    
    now = datetime.utcnow()
    events = [
        {"title": "Salsa Night", "event_type": "Social Meetup", "city": "Istanbul", "description": "Weekly salsa", "start_time": now + timedelta(days=2), "end_time": now + timedelta(days=2, hours=4), "dance_styles": ["Salsa"], "created_by": "system", "created_at": now, "attendees": [], "comments": []},
        {"title": "Bachata Workshop", "event_type": "Workshop", "city": "New York", "description": "Beginner workshop", "start_time": now + timedelta(days=5), "end_time": now + timedelta(days=5, hours=2), "dance_styles": ["Bachata"], "created_by": "system", "created_at": now, "attendees": [], "comments": []},
        {"title": "Tango Milonga", "event_type": "Dance Night", "city": "Berlin", "description": "Traditional milonga", "start_time": now + timedelta(days=7), "end_time": now + timedelta(days=7, hours=5), "dance_styles": ["Tango"], "created_by": "system", "created_at": now, "attendees": [], "comments": []},
    ]
    
    for event in events:
        if not await db.events.find_one({"title": event["title"]}):
            await db.events.insert_one(event)
    
    print("✅ Database seeded", flush=True)
    return {"message": "Seeded", "users_added": 5, "events_added": 3}

# ===== HEALTH CHECK =====
@api_router.get("/health")
async def health():
    return {"status": "ok", "db": DB_NAME, "version": "3.0"}

# --- APP SETUP ---
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print(f"🚀 DanceBuddy API v3.0 | Database: {DB_NAME}", flush=True)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
