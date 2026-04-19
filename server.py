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

# MongoDB connection - with fallback for safety
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'dancebuddy')]

# Security - supports both bcrypt and argon2 (existing users may have either hash)
pwd_context = CryptContext(schemes=["bcrypt", "argon2"], deprecated="auto")
SECRET_KEY = os.environ.get("SECRET_KEY", "dancebuddy-secret-key-2025")
ADMIN_KEY = os.environ.get("ADMIN_KEY", "dancebuddy-admin-emergency-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

security = HTTPBearer()
app = FastAPI(title="DanceBuddy API", version="3.2")
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

# ===== MODELS =====

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

class AdminResetRequest(BaseModel):
    admin_key: str
    email: EmailStr
    new_password: str

# ===== HELPERS =====

def verify_password(plain, hashed): return pwd_context.verify(plain, hashed)
def get_password_hash(password): return pwd_context.hash(password)

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
    except Exception:
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
    except Exception:
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

# ===== AUTH ROUTES =====

@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserRegister):
    if user_data.city not in FIXED_CITIES:
        raise HTTPException(status_code=400, detail=f"Invalid city. Must be one of: {', '.join(FIXED_CITIES)}")
    
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
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    return {
        "access_token": create_access_token({"sub": str(user["_id"])}),
        "token_type": "bearer",
        "user": format_user_response(user)
    }

# ===== PASSWORD RESET =====

@api_router.post("/auth/forgot-password")
async def forgot_password(data: ForgotPasswordRequest):
    """Request password reset. Returns reset_token directly in DEV mode (no SMTP configured)."""
    user = await db.users.find_one({"email": data.email})
    if not user:
        return {"success": True, "message": "If this email exists, reset instructions were sent."}
    
    reset_token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(hours=1)
    
    await db.password_resets.insert_one({
        "email": data.email,
        "token": reset_token,
        "expires": expires,
        "used": False,
        "created_at": datetime.utcnow()
    })
    
    logger.info(f"Password reset requested for {data.email}. Token: {reset_token}")
    return {
        "success": True,
        "message": "If this email exists, reset instructions were sent.",
        "reset_token": reset_token,
        "dev_mode": True
    }

@api_router.post("/auth/reset-password")
async def reset_password(data: ResetPasswordRequest):
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    reset_record = await db.password_resets.find_one({"token": data.token, "used": False})
    if not reset_record:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    if reset_record["expires"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Reset token has expired")
    
    await db.users.update_one(
        {"email": reset_record["email"]},
        {"$set": {"password_hash": get_password_hash(data.new_password)}}
    )
    
    await db.password_resets.update_one(
        {"_id": reset_record["_id"]},
        {"$set": {"used": True, "used_at": datetime.utcnow()}}
    )
    
    return {"success": True, "message": "Password reset successfully. You can now sign in."}

@api_router.post("/auth/admin-reset-password")
async def admin_reset_password(data: AdminResetRequest):
    """EMERGENCY: Reset any user's password using the ADMIN_KEY."""
    if data.admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    user = await db.users.find_one({"email": data.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"password_hash": get_password_hash(data.new_password)}}
    )
    
    logger.info(f"Admin reset password for user: {data.email}")
    return {"success": True, "message": f"Password reset for {data.email}"}

# ===== USER ROUTES =====

@api_router.get("/users/me")
async def get_my_profile(current_user = Depends(get_current_user)):
    return format_user_response(current_user)

@api_router.put("/users/me")
async def update_profile(user_data: UserUpdate, current_user = Depends(get_current_user)):
    update_dict = {}
    
    if user_data.name is not None:
        update_dict["name"] = user_data.name
    if user_data.bio is not None:
        update_dict["bio"] = user_data.bio
    if user_data.photo is not None:
        update_dict["photo"] = user_data.photo
    if user_data.gallery is not None:
        update_dict["gallery"] = user_data.gallery[:5]
    if user_data.city is not None:
        if user_data.city not in FIXED_CITIES:
            raise HTTPException(status_code=400, detail=f"Invalid city. Must be one of: {', '.join(FIXED_CITIES)}")
        update_dict["city"] = user_data.city
    if user_data.dance_level is not None:
        if user_data.dance_level not in DANCE_LEVELS:
            raise HTTPException(status_code=400, detail=f"Invalid dance level. Must be one of: {', '.join(DANCE_LEVELS)}")
        update_dict["dance_level"] = user_data.dance_level
    if user_data.favorite_dance_music is not None:
        update_dict["favorite_dance_music"] = user_data.favorite_dance_music
    if user_data.dance_styles is not None:
        update_dict["dance_styles"] = user_data.dance_styles
    
    if update_dict:
        await db.users.update_one({"_id": current_user["_id"]}, {"$set": update_dict})
    
    updated = await db.users.find_one({"_id": current_user["_id"]})
    return format_user_response(updated)

@api_router.delete("/users/me")
async def delete_my_account(current_user = Depends(get_current_user)):
    """Delete my account and all associated data."""
    user_id = str(current_user["_id"])
    user_obj_id = current_user["_id"]
    
    await db.partner_requests.delete_many({"user_id": user_id})
    await db.memories.delete_many({"user_id": user_id})
    
    await db.events.update_many(
        {},
        {"$pull": {"attendees": {"user_id": user_id}, "comments": {"user_id": user_id}}}
    )
    await db.memories.update_many({}, {"$pull": {"likes": user_id}})
    await db.partner_requests.update_many({}, {"$pull": {"interested_users": {"user_id": user_id}}})
    
    await db.events.delete_many({"created_by": user_id})
    await db.users.delete_one({"_id": user_obj_id})
    await db.password_resets.delete_many({"email": current_user.get("email")})
    
    logger.info(f"User account deleted: {current_user.get('email')}")
    return {"success": True, "message": "Account deleted successfully"}

@api_router.get("/users")
async def get_all_users(city: Optional[str] = None, current_user = Depends(get_current_user)):
    query = {"_id": {"$ne": current_user["_id"]}}
    if city and city in FIXED_CITIES:
        query["city"] = city
    users = await db.users.find(query).limit(100).to_list(100)
    return [format_user_response(u) for u in users]

@api_router.get("/users/{user_id}")
async def get_user_detail(user_id: str, current_user = Depends(get_current_user)):
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return format_user_response(user)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID")

# ===== PUBLIC ROUTES (Guest Access) =====

@api_router.get("/public/events")
async def get_public_events(city: Optional[str] = None):
    now = datetime.utcnow()
    query = {"end_time": {"$gt": now}}
    if city and city in FIXED_CITIES:
        query["city"] = city
    events = await db.events.find(query).sort("start_time", 1).limit(50).to_list(50)
    return [format_event_response(e, include_attendees=False, include_comments=False) for e in events]

@api_router.get("/public/cities")
async def get_cities():
    return {"cities": FIXED_CITIES}

@api_router.get("/public/dance-styles")
async def get_dance_styles():
    return {"dance_styles": DANCE_STYLES}

# ===== EVENT ROUTES =====

@api_router.get("/events")
async def get_events(city: Optional[str] = None, current_user = Depends(get_current_user)):
    now = datetime.utcnow()
    query = {"end_time": {"$gt": now}}
    if city and city in FIXED_CITIES:
        query["city"] = city
    events = await db.events.find(query).sort("start_time", 1).limit(50).to_list(50)
    return [format_event_response(e, include_attendees=True, include_comments=True) for e in events]

@api_router.post("/events")
async def create_event(event_data: EventCreate, current_user = Depends(get_current_user)):
    if event_data.city not in FIXED_CITIES:
        raise HTTPException(status_code=400, detail="Invalid city")
    if event_data.event_type not in EVENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid event type. Must be one of: {', '.join(EVENT_TYPES)}")
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
    return format_event_response(event, include_attendees=True, include_comments=True)

@api_router.get("/events/{event_id}")
async def get_event_detail(event_id: str, current_user = Depends(get_current_user)):
    try:
        event = await db.events.find_one({"_id": ObjectId(event_id)})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return format_event_response(event, include_attendees=True, include_comments=True)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid event ID")

@api_router.post("/events/{event_id}/join")
async def join_event(event_id: str, current_user = Depends(get_current_user)):
    try:
        event = await db.events.find_one({"_id": ObjectId(event_id)})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        user_id = str(current_user["_id"])
        attendees = event.get("attendees", []) or []
        
        if any(a.get("user_id") == user_id for a in attendees):
            raise HTTPException(status_code=400, detail="Already joined this event")
        
        attendee_info = {
            "user_id": user_id,
            "name": current_user.get("name", ""),
            "photo": current_user.get("photo"),
            "joined_at": datetime.utcnow()
        }
        
        await db.events.update_one(
            {"_id": ObjectId(event_id)},
            {"$push": {"attendees": attendee_info}}
        )
        
        return {"success": True, "message": "Joined event"}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid event ID")

@api_router.delete("/events/{event_id}/join")
async def leave_event(event_id: str, current_user = Depends(get_current_user)):
    try:
        user_id = str(current_user["_id"])
        await db.events.update_one(
            {"_id": ObjectId(event_id)},
            {"$pull": {"attendees": {"user_id": user_id}}}
        )
        return {"success": True, "message": "Left event"}
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid event ID")

@api_router.get("/events/{event_id}/attendees")
async def get_event_attendees(event_id: str, current_user = Depends(get_current_user)):
    try:
        event = await db.events.find_one({"_id": ObjectId(event_id)})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return {"attendees": event.get("attendees", []) or []}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid event ID")

@api_router.post("/events/{event_id}/comments")
async def add_comment(event_id: str, comment_data: EventComment, current_user = Depends(get_current_user)):
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
        
        await db.events.update_one(
            {"_id": ObjectId(event_id)},
            {"$push": {"comments": comment}}
        )
        
        return comment
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid event ID")

@api_router.get("/events/{event_id}/comments")
async def get_comments(event_id: str, current_user = Depends(get_current_user)):
    try:
        event = await db.events.find_one({"_id": ObjectId(event_id)})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return {"comments": event.get("comments", []) or []}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid event ID")

# ===== PARTNER REQUESTS =====

@api_router.get("/partner-requests")
async def get_partner_requests(city: Optional[str] = None, dance_style: Optional[str] = None, current_user = Depends(get_current_user)):
    query = {}
    if city and city in FIXED_CITIES:
        query["city"] = city
    if dance_style:
        query["dance_style"] = dance_style
    
    requests = await db.partner_requests.find(query).sort("created_at", -1).limit(50).to_list(50)
    
    result = []
    for r in requests:
        interested = r.get("interested_users", []) or []
        is_mine = r.get("user_id") == str(current_user["_id"])
        result.append({
            "id": str(r["_id"]),
            "title": r.get("title", ""),
            "description": r.get("description", ""),
            "city": r.get("city", ""),
            "dance_style": r.get("dance_style", ""),
            "looking_for_level": r.get("looking_for_level"),
            "user_id": r.get("user_id"),
            "user_name": r.get("user_name", ""),
            "user_photo": r.get("user_photo"),
            "created_at": r.get("created_at"),
            "interested_count": len(interested),
            "is_interested": any(u.get("user_id") == str(current_user["_id"]) for u in interested),
            "is_mine": is_mine,
        })
    
    return result

@api_router.post("/partner-requests")
async def create_partner_request(request_data: PartnerRequestCreate, current_user = Depends(get_current_user)):
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
        "interested_users": [],
        "created_at": datetime.utcnow()
    }
    
    result = await db.partner_requests.insert_one(partner_request)
    
    return {
        "id": str(result.inserted_id),
        "title": partner_request["title"],
        "description": partner_request["description"],
        "city": partner_request["city"],
        "dance_style": partner_request["dance_style"],
        "looking_for_level": partner_request["looking_for_level"],
        "user_id": partner_request["user_id"],
        "user_name": partner_request["user_name"],
        "user_photo": partner_request["user_photo"],
        "created_at": partner_request["created_at"],
        "interested_count": 0,
        "is_interested": False,
        "is_mine": True,
    }

@api_router.delete("/partner-requests/{request_id}")
async def delete_partner_request(request_id: str, current_user = Depends(get_current_user)):
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
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid request ID")

@api_router.post("/partner-requests/{request_id}/interest")
async def express_interest(request_id: str, current_user = Depends(get_current_user)):
    """Express interest in a partner request (user taps 'Interested')."""
    try:
        request = await db.partner_requests.find_one({"_id": ObjectId(request_id)})
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        user_id = str(current_user["_id"])
        
        if request.get("user_id") == user_id:
            raise HTTPException(status_code=400, detail="Cannot express interest in your own request")
        
        interested_users = request.get("interested_users", []) or []
        
        if any(u.get("user_id") == user_id for u in interested_users):
            return {"success": True, "message": "Already interested", "is_interested": True}
        
        interest = {
            "user_id": user_id,
            "name": current_user.get("name", ""),
            "photo": current_user.get("photo"),
            "city": current_user.get("city", ""),
            "dance_level": current_user.get("dance_level", ""),
            "created_at": datetime.utcnow()
        }
        
        await db.partner_requests.update_one(
            {"_id": ObjectId(request_id)},
            {"$push": {"interested_users": interest}}
        )
        
        return {"success": True, "message": "Interest expressed", "is_interested": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error expressing interest: {e}")
        raise HTTPException(status_code=400, detail="Invalid request ID")

@api_router.delete("/partner-requests/{request_id}/interest")
async def remove_interest(request_id: str, current_user = Depends(get_current_user)):
    """Remove interest from a partner request."""
    try:
        user_id = str(current_user["_id"])
        await db.partner_requests.update_one(
            {"_id": ObjectId(request_id)},
            {"$pull": {"interested_users": {"user_id": user_id}}}
        )
        return {"success": True, "is_interested": False}
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid request ID")

@api_router.get("/partner-requests/{request_id}/interested")
async def get_interested_users(request_id: str, current_user = Depends(get_current_user)):
    """Get list of users interested in this request. Only accessible by the owner."""
    try:
        request = await db.partner_requests.find_one({"_id": ObjectId(request_id)})
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        if request.get("user_id") != str(current_user["_id"]):
            raise HTTPException(status_code=403, detail="Only the request owner can see interested users")
        
        return request.get("interested_users", []) or []
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid request ID")

# ===== DANCE MEMORIES =====

@api_router.get("/memories")
async def get_memories(memory_type: Optional[str] = None, current_user = Depends(get_current_user)):
    query = {}
    if memory_type and memory_type in MEMORY_TYPES:
        query["memory_type"] = memory_type
    
    memories = await db.memories.find(query).sort("created_at", -1).limit(50).to_list(50)
    
    result = []
    for m in memories:
        result.append({
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
        })
    
    return result

@api_router.post("/memories")
async def create_memory(memory_data: MemoryCreate, current_user = Depends(get_current_user)):
    if memory_data.memory_type not in MEMORY_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid memory type. Must be one of: {', '.join(MEMORY_TYPES)}")
    
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
    
    return {
        "id": str(result.inserted_id),
        "memory_type": memory["memory_type"],
        "content": memory["content"],
        "city": memory["city"],
        "user_id": memory["user_id"],
        "user_name": memory["user_name"],
        "user_photo": memory["user_photo"],
        "likes": memory["likes"],
        "likes_count": 0,
        "created_at": memory["created_at"]
    }

@api_router.post("/memories/{memory_id}/like")
async def like_memory(memory_id: str, current_user = Depends(get_current_user)):
    try:
        user_id = str(current_user["_id"])
        memory = await db.memories.find_one({"_id": ObjectId(memory_id)})
        
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        likes = memory.get("likes", []) or []
        
        if user_id in likes:
            await db.memories.update_one(
                {"_id": ObjectId(memory_id)},
                {"$pull": {"likes": user_id}}
            )
            return {"liked": False, "likes_count": len(likes) - 1}
        else:
            await db.memories.update_one(
                {"_id": ObjectId(memory_id)},
                {"$push": {"likes": user_id}}
            )
            return {"liked": True, "likes_count": len(likes) + 1}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid memory ID")

@api_router.delete("/memories/{memory_id}")
async def delete_memory(memory_id: str, current_user = Depends(get_current_user)):
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
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid memory ID")

# ===== SETUP =====

app.include_router(api_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/health")
async def health():
    return {"status": "ok", "version": "3.2", "cities_count": len(FIXED_CITIES)}
