from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Literal
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from bson import ObjectId
from enum import Enum
import secrets

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'dancebuddy')]

pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")
SECRET_KEY = os.environ.get("SECRET_KEY", "dancebuddy-secret-key-2025")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

security = HTTPBearer()
app = FastAPI(title="DanceBuddy API", version="3.1")
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    city: str
    bio: Optional[str] = ""
    photo: Optional[str] = None
    gallery: Optional[List[str]] = []
    dance_level: str = "Beginner"
    favorite_dance_music: Optional[str] = ""
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

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    city: str
    bio: str = ""
    photo: Optional[str] = None
    gallery: List[str] = []
    dance_level: str = "Beginner"
    favorite_dance_music: str = ""
    dance_styles: List[str] = []
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

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

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

def verify_password(plain, hashed):
    try:
        return pwd_context.verify(plain, hashed)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Authentication failed")

async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))):
    if not credentials:
        return None
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        return user
    except:
        return None

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

def format_partner_request(request: dict) -> dict:
    return {
        "id": str(request["_id"]),
        "title": request.get("title", ""),
        "description": request.get("description", ""),
        "city": request.get("city", ""),
        "dance_style": request.get("dance_style", ""),
        "looking_for_level": request.get("looking_for_level"),
        "user_id": request.get("user_id"),
        "user_name": request.get("user_name", ""),
        "user_photo": request.get("user_photo"),
        "created_at": request.get("created_at"),
        "interested_users": request.get("interested_users", []) or [],
        "interested_count": len(request.get("interested_users", []) or []),
    }

def format_memory(memory: dict) -> dict:
    return {
        "id": str(memory["_id"]),
        "memory_type": memory.get("memory_type", ""),
        "content": memory.get("content", ""),
        "city": memory.get("city"),
        "user_id": memory.get("user_id"),
        "user_name": memory.get("user_name", ""),
        "user_photo": memory.get("user_photo"),
        "likes": memory.get("likes", []) or [],
        "likes_count": len(memory.get("likes", []) or []),
        "created_at": memory.get("created_at"),
    }

@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserRegister):
    if user_data.city not in FIXED_CITIES:
        raise HTTPException(status_code=400, detail=f"Invalid city")
    if await db.users.find_one({"email": user_data.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    user_dict = {
        "name": user_data.name,
        "email": user_data.email,
        "password_hash": get_password_hash(user_data.password),
        "city": user_data.city,
        "bio": user_data.bio or "",
        "photo": user_data.photo,
        "gallery": (user_data.gallery or [])[:5],
        "dance_level": user_data.dance_level if user_data.dance_level in DANCE_LEVELS else "Beginner",
        "favorite_dance_music": user_data.favorite_dance_music or "",
        "dance_styles": user_data.dance_styles or [],
        "created_at": datetime.utcnow()
    }
    result = await db.users.insert_one(user_dict)
    user_dict["_id"] = result.inserted_id
    return {
        "access_token": create_access_token({"sub": str(result.inserted_id)}),
        "token_type": "bearer",
        "user": format_user_response(user_dict)
    }

@api_router.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {
        "access_token": create_access_token({"sub": str(user["_id"])}),
        "token_type": "bearer",
        "user": format_user_response(user)
    }

@api_router.post("/auth/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    user = await db.users.find_one({"email": request.email})
    if not user:
        return {"message": "If an account exists, reset instructions will be sent."}
    reset_token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(hours=1)
    await db.password_resets.delete_many({"email": request.email})
    await db.password_resets.insert_one({
        "email": request.email,
        "token": reset_token,
        "expires": expires,
        "created_at": datetime.utcnow()
    })
    logger.info(f"Password reset token for {request.email}: {reset_token}")
    return {"message": "If an account exists, reset instructions will be sent."}

@api_router.post("/auth/reset-password")
async def reset_password(request: ResetPasswordRequest):
    reset_record = await db.password_resets.find_one({"token": request.token})
    if not reset_record:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    if reset_record["expires"] < datetime.utcnow():
        await db.password_resets.delete_one({"token": request.token})
        raise HTTPException(status_code=400, detail="Reset token has expired")
    new_hash = get_password_hash(request.new_password)
    await db.users.update_one({"email": reset_record["email"]}, {"$set": {"password_hash": new_hash}})
    await db.password_resets.delete_one({"token": request.token})
    return {"message": "Password has been reset successfully"}

@api_router.get("/users/me")
async def get_my_profile(current_user = Depends(get_current_user)):
    return format_user_response(current_user)

@api_router.put("/users/me")
async def update_my_profile(updates: UserUpdate, current_user = Depends(get_current_user)):
    update_data = {}
    if updates.name: update_data["name"] = updates.name
    if updates.bio is not None: update_data["bio"] = updates.bio
    if updates.photo is not None: update_data["photo"] = updates.photo
    if updates.gallery is not None: update_data["gallery"] = updates.gallery[:5]
    if updates.city and updates.city in FIXED_CITIES: update_data["city"] = updates.city
    if updates.dance_level and updates.dance_level in DANCE_LEVELS: update_data["dance_level"] = updates.dance_level
    if updates.favorite_dance_music is not None: update_data["favorite_dance_music"] = updates.favorite_dance_music
    if updates.dance_styles is not None: update_data["dance_styles"] = updates.dance_styles
    if update_data:
        await db.users.update_one({"_id": current_user["_id"]}, {"$set": update_data})
    updated_user = await db.users.find_one({"_id": current_user["_id"]})
    return format_user_response(updated_user)

@api_router.get("/users")
async def get_users(city: Optional[str] = None, current_user = Depends(get_current_user)):
    query = {}
    if city and city in FIXED_CITIES:
        query["city"] = city
    users = await db.users.find(query).sort("created_at", -1).limit(100).to_list(100)
    return [format_user_response(u) for u in users]

@api_router.get("/users/{user_id}")
async def get_user(user_id: str, current_user = Depends(get_current_user)):
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return format_user_response(user)
    except:
        raise HTTPException(status_code=404, detail="User not found")

@api_router.get("/public/events")
async def get_public_events(city: Optional[str] = None):
    now = datetime.utcnow()
    query = {"end_time": {"$gte": now}}
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

@api_router.get("/events")
async def get_events(city: Optional[str] = None, current_user = Depends(get_current_user)):
    now = datetime.utcnow()
    query = {"end_time": {"$gte": now}}
    if city and city in FIXED_CITIES:
        query["city"] = city
    events = await db.events.find(query).sort("start_time", 1).limit(50).to_list(50)
    return [format_event_response(e, include_attendees=True) for e in events]

@api_router.get("/events/{event_id}")
async def get_event(event_id: str, current_user = Depends(get_current_user)):
    try:
        event = await db.events.find_one({"_id": ObjectId(event_id)})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return format_event_response(event, include_attendees=True, include_comments=True)
    except:
        raise HTTPException(status_code=404, detail="Event not found")

@api_router.post("/events")
async def create_event(event_data: EventCreate, current_user = Depends(get_current_user)):
    if event_data.city not in FIXED_CITIES:
        raise HTTPException(status_code=400, detail="Invalid city")
    if event_data.end_time <= event_data.start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")
    event_dict = {
        "title": event_data.title,
        "event_type": event_data.event_type if event_data.event_type in EVENT_TYPES else "Dance Night",
        "city": event_data.city,
        "description": event_data.description or "",
        "start_time": event_data.start_time,
        "end_time": event_data.end_time,
        "dance_styles": event_data.dance_styles or [],
        "created_by": str(current_user["_id"]),
        "attendees": [str(current_user["_id"])],
        "comments": [],
        "created_at": datetime.utcnow()
    }
    result = await db.events.insert_one(event_dict)
    event_dict["_id"] = result.inserted_id
    return format_event_response(event_dict, include_attendees=True)

@api_router.post("/events/{event_id}/join")
async def join_event(event_id: str, current_user = Depends(get_current_user)):
    try:
        event = await db.events.find_one({"_id": ObjectId(event_id)})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        user_id = str(current_user["_id"])
        attendees = event.get("attendees", []) or []
        if user_id in attendees:
            raise HTTPException(status_code=400, detail="Already joined")
        await db.events.update_one({"_id": ObjectId(event_id)}, {"$push": {"attendees": user_id}})
        return {"message": "Joined event"}
    except HTTPException:
        raise
    except:
        raise HTTPException(status_code=404, detail="Event not found")

@api_router.delete("/events/{event_id}/join")
async def leave_event(event_id: str, current_user = Depends(get_current_user)):
    try:
        user_id = str(current_user["_id"])
        await db.events.update_one({"_id": ObjectId(event_id)}, {"$pull": {"attendees": user_id}})
        return {"message": "Left event"}
    except:
        raise HTTPException(status_code=404, detail="Event not found")

@api_router.get("/events/{event_id}/attendees")
async def get_event_attendees(event_id: str, current_user = Depends(get_current_user)):
    try:
        event = await db.events.find_one({"_id": ObjectId(event_id)})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        attendee_ids = event.get("attendees", []) or []
        attendees = []
        for aid in attendee_ids:
            try:
                user = await db.users.find_one({"_id": ObjectId(aid)})
                if user:
                    attendees.append(format_user_response(user))
            except:
                pass
        return attendees
    except:
        raise HTTPException(status_code=404, detail="Event not found")

@api_router.post("/events/{event_id}/comments")
async def add_comment(event_id: str, comment_data: EventComment, current_user = Depends(get_current_user)):
    try:
        comment = {
            "user_id": str(current_user["_id"]),
            "user_name": current_user.get("name", ""),
            "user_photo": current_user.get("photo"),
            "comment": comment_data.comment,
            "created_at": datetime.utcnow()
        }
        await db.events.update_one({"_id": ObjectId(event_id)}, {"$push": {"comments": comment}})
        return comment
    except:
        raise HTTPException(status_code=404, detail="Event not found")

@api_router.get("/events/{event_id}/comments")
async def get_comments(event_id: str, current_user = Depends(get_current_user)):
    try:
        event = await db.events.find_one({"_id": ObjectId(event_id)})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return event.get("comments", []) or []
    except:
        raise HTTPException(status_code=404, detail="Event not found")

@api_router.get("/partner-requests")
async def get_partner_requests(city: Optional[str] = None, dance_style: Optional[str] = None, current_user = Depends(get_current_user)):
    query = {}
    if city and city in FIXED_CITIES:
        query["city"] = city
    if dance_style and dance_style in DANCE_STYLES:
        query["dance_style"] = dance_style
    requests = await db.partner_requests.find(query).sort("created_at", -1).limit(50).to_list(50)
    return [format_partner_request(r) for r in requests]

@api_router.post("/partner-requests")
async def create_partner_request(request_data: PartnerRequestCreate, current_user = Depends(get_current_user)):
    if request_data.city not in FIXED_CITIES:
        raise HTTPException(status_code=400, detail="Invalid city")
    if request_data.dance_style not in DANCE_STYLES:
        raise HTTPException(status_code=400, detail="Invalid dance style")
    request_dict = {
        "title": request_data.title,
        "description": request_data.description or "",
        "city": request_data.city,
        "dance_style": request_data.dance_style,
        "looking_for_level": request_data.looking_for_level if request_data.looking_for_level in DANCE_LEVELS else None,
        "user_id": str(current_user["_id"]),
        "user_name": current_user.get("name", ""),
        "user_photo": current_user.get("photo"),
        "interested_users": [],
        "created_at": datetime.utcnow()
    }
    result = await db.partner_requests.insert_one(request_dict)
    request_dict["_id"] = result.inserted_id
    return format_partner_request(request_dict)

@api_router.delete("/partner-requests/{request_id}")
async def delete_partner_request(request_id: str, current_user = Depends(get_current_user)):
    try:
        request = await db.partner_requests.find_one({"_id": ObjectId(request_id)})
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        if request["user_id"] != str(current_user["_id"]):
            raise HTTPException(status_code=403, detail="Not authorized")
        await db.partner_requests.delete_one({"_id": ObjectId(request_id)})
        return {"message": "Request deleted"}
    except HTTPException:
        raise
    except:
        raise HTTPException(status_code=404, detail="Request not found")

@api_router.post("/partner-requests/{request_id}/interest")
async def express_interest(request_id: str, current_user = Depends(get_current_user)):
    try:
        request = await db.partner_requests.find_one({"_id": ObjectId(request_id)})
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        user_id = str(current_user["_id"])
        if request["user_id"] == user_id:
            raise HTTPException(status_code=400, detail="Cannot express interest in your own request")
        interested = request.get("interested_users", []) or []
        if user_id in interested:
            raise HTTPException(status_code=400, detail="Already expressed interest")
        await db.partner_requests.update_one({"_id": ObjectId(request_id)}, {"$push": {"interested_users": user_id}})
        return {"message": "Interest expressed"}
    except HTTPException:
        raise
    except:
        raise HTTPException(status_code=404, detail="Request not found")

@api_router.delete("/partner-requests/{request_id}/interest")
async def remove_interest(request_id: str, current_user = Depends(get_current_user)):
    try:
        user_id = str(current_user["_id"])
        await db.partner_requests.update_one({"_id": ObjectId(request_id)}, {"$pull": {"interested_users": user_id}})
        return {"message": "Interest removed"}
    except:
        raise HTTPException(status_code=404, detail="Request not found")

@api_router.get("/partner-requests/{request_id}/interested")
async def get_interested_users(request_id: str, current_user = Depends(get_current_user)):
    try:
        request = await db.partner_requests.find_one({"_id": ObjectId(request_id)})
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        if request["user_id"] != str(current_user["_id"]):
            raise HTTPException(status_code=403, detail="Only owner can view")
        interested_ids = request.get("interested_users", []) or []
        users = []
        for uid in interested_ids:
            try:
                user = await db.users.find_one({"_id": ObjectId(uid)})
                if user:
                    users.append(format_user_response(user))
            except:
                pass
        return users
    except HTTPException:
        raise
    except:
        raise HTTPException(status_code=404, detail="Request not found")

@api_router.get("/memories")
async def get_memories(memory_type: Optional[str] = None, current_user = Depends(get_current_user)):
    query = {}
    if memory_type and memory_type in MEMORY_TYPES:
        query["memory_type"] = memory_type
    memories = await db.memories.find(query).sort("created_at", -1).limit(50).to_list(50)
    return [format_memory(m) for m in memories]

@api_router.post("/memories")
async def create_memory(memory_data: MemoryCreate, current_user = Depends(get_current_user)):
    if memory_data.memory_type not in MEMORY_TYPES:
        raise HTTPException(status_code=400, detail="Invalid memory type")
    if memory_data.city and memory_data.city not in FIXED_CITIES:
        raise HTTPException(status_code=400, detail="Invalid city")
    memory_dict = {
        "memory_type": memory_data.memory_type,
        "content": memory_data.content,
        "city": memory_data.city,
        "user_id": str(current_user["_id"]),
        "user_name": current_user.get("name", ""),
        "user_photo": current_user.get("photo"),
        "likes": [],
        "created_at": datetime.utcnow()
    }
    result = await db.memories.insert_one(memory_dict)
    memory_dict["_id"] = result.inserted_id
    return format_memory(memory_dict)

@api_router.post("/memories/{memory_id}/like")
async def like_memory(memory_id: str, current_user = Depends(get_current_user)):
    try:
        memory = await db.memories.find_one({"_id": ObjectId(memory_id)})
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        user_id = str(current_user["_id"])
        likes = memory.get("likes", []) or []
        if user_id in likes:
            await db.memories.update_one({"_id": ObjectId(memory_id)}, {"$pull": {"likes": user_id}})
            return {"message": "Unliked", "liked": False}
        else:
            await db.memories.update_one({"_id": ObjectId(memory_id)}, {"$push": {"likes": user_id}})
            return {"message": "Liked", "liked": True}
    except:
        raise HTTPException(status_code=404, detail="Memory not found")

@api_router.delete("/memories/{memory_id}")
async def delete_memory(memory_id: str, current_user = Depends(get_current_user)):
    try:
        memory = await db.memories.find_one({"_id": ObjectId(memory_id)})
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        if memory["user_id"] != str(current_user["_id"]):
            raise HTTPException(status_code=403, detail="Not authorized")
        await db.memories.delete_one({"_id": ObjectId(memory_id)})
        return {"message": "Memory deleted"}
    except HTTPException:
        raise
    except:
        raise HTTPException(status_code=404, detail="Memory not found")

@api_router.post("/seed")
async def seed_database():
    test_users = [
        {"name": "Maria Garcia", "email": "maria@example.com", "city": "Berlin", "dance_level": "Advanced", "dance_styles": ["Salsa", "Bachata"]},
        {"name": "John Smith", "email": "john@example.com", "city": "New York", "dance_level": "Intermediate", "dance_styles": ["Tango"]},
        {"name": "Sophie Laurent", "email": "sophie@example.com", "city": "Paris", "dance_level": "Beginner", "dance_styles": ["Salsa"]},
    ]
    created_users = []
    for user_data in test_users:
        existing = await db.users.find_one({"email": user_data["email"]})
        if not existing:
            user_dict = {
                **user_data,
                "password_hash": get_password_hash("test123"),
                "bio": f"Dancer from {user_data['city']}",
                "photo": None,
                "gallery": [],
                "favorite_dance_music": "",
                "created_at": datetime.utcnow()
            }
            result = await db.users.insert_one(user_dict)
            created_users.append(str(result.inserted_id))
    now = datetime.utcnow()
    test_events = [
        {"title": "Friday Salsa Night", "event_type": "Dance Night", "city": "Berlin", "dance_styles": ["Salsa"]},
        {"title": "Tango Workshop", "event_type": "Workshop", "city": "New York", "dance_styles": ["Tango"]},
    ]
    for i, event_data in enumerate(test_events):
        existing = await db.events.find_one({"title": event_data["title"]})
        if not existing:
            event_dict = {
                **event_data,
                "description": f"Join us for {event_data['event_type']}!",
                "start_time": now + timedelta(days=i+1, hours=19),
                "end_time": now + timedelta(days=i+1, hours=23),
                "created_by": created_users[0] if created_users else "system",
                "attendees": [],
                "comments": [],
                "created_at": datetime.utcnow()
            }
            await db.events.insert_one(event_dict)
    return {"message": "Database seeded", "users_created": len(created_users)}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "DanceBuddy API v3.1", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "3.1"}
