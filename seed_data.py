"""
Seed Script for Dance Buddy App - COMPREHENSIVE VERSION
Creates production-ready demo data for App Store screenshots
"""
import asyncio
import random
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from bson import ObjectId
import os
from dotenv import load_dotenv

load_dotenv()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "test_database")
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# High-quality images from Unsplash/Pexels
PROFILE_IMAGES = {
    "male": [
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400",
        "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=400",
        "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400",
        "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=400",
        "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=400",
        "https://images.unsplash.com/photo-1463453091185-61582044d556?w=400",
        "https://images.unsplash.com/photo-1552058544-f2b08422138a?w=400",
    ],
    "female": [
        "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400",
        "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=400",
        "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400",
        "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=400",
        "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=400",
        "https://images.unsplash.com/photo-1488426862026-3ee34a7d66df?w=400",
        "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?w=400",
        "https://images.unsplash.com/photo-1502823403499-6ccfcf4fb453?w=400",
    ]
}

SCHOOL_IMAGES = [
    "https://images.unsplash.com/photo-1549895058-36748fa6c6a7?w=600",
    "https://images.unsplash.com/photo-1687087172783-3a9f16246579?w=600",
    "https://images.unsplash.com/photo-1566596343373-30675086c273?w=600",
    "https://images.unsplash.com/photo-1526568929-7cdd510e77fd?w=600",
    "https://images.pexels.com/photos/8133007/pexels-photo-8133007.jpeg?w=600",
]

EVENT_IMAGES = [
    "https://images.pexels.com/photos/270789/pexels-photo-270789.jpeg?w=800",
    "https://images.pexels.com/photos/14699922/pexels-photo-14699922.jpeg?w=800",
    "https://images.pexels.com/photos/27240398/pexels-photo-27240398.jpeg?w=800",
    "https://images.unsplash.com/photo-1504609813442-a8924e83f76e?w=800",
    "https://images.unsplash.com/photo-1529229504105-4ea795dcbf59?w=800",
    "https://images.pexels.com/photos/31780692/pexels-photo-31780692.jpeg?w=800",
    "https://images.pexels.com/photos/2057274/pexels-photo-2057274.jpeg?w=800",
    "https://images.unsplash.com/photo-1547153760-18fc86324498?w=800",
    "https://images.unsplash.com/photo-1568557412756-7d219873dd11?w=800",
    "https://images.pexels.com/photos/8281148/pexels-photo-8281148.jpeg?w=800",
    "https://images.unsplash.com/photo-1545128485-c400e7702796?w=800",
    "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?w=800",
]

# Dance Schools Data
SCHOOLS_DATA = [
    {
        "name": "Miami Salsa Academy",
        "email": "info@miamisalsaacademy.com",
        "city": "Miami",
        "latitude": 25.7617,
        "longitude": -80.1918,
        "description": "Miami's premier Latin dance academy featuring world-class instructors from Cuba and Puerto Rico. We specialize in authentic Salsa On1, On2, and Cuban-style dancing with classes for all levels from absolute beginners to professional performers.",
        "address": "1234 Ocean Drive, Miami Beach, FL 33139",
        "phone": "+1 (305) 555-0123",
        "website": "https://miamisalsaacademy.com",
    },
    {
        "name": "Berlin Tango Haus",
        "email": "contact@berlintangohaus.de",
        "city": "Berlin",
        "latitude": 52.5200,
        "longitude": 13.4050,
        "description": "Experience the passion of Argentine Tango in the heart of Berlin. Our authentic milongas and classes bring the spirit of Buenos Aires to Europe. Join our vibrant community of tango enthusiasts from around the world.",
        "address": "Friedrichstraße 112, 10117 Berlin, Germany",
        "phone": "+49 30 555 0456",
        "website": "https://berlintangohaus.de",
    },
    {
        "name": "London Latin Dance Co.",
        "email": "hello@londonlatindance.co.uk",
        "city": "London",
        "latitude": 51.5074,
        "longitude": -0.1278,
        "description": "London's most exciting Latin dance company offering Salsa, Bachata, and Kizomba classes in central London. Our professional team includes champions from Latin America and Europe with over 50 years combined experience.",
        "address": "45 Covent Garden, London WC2E 8RF, UK",
        "phone": "+44 20 7555 0789",
        "website": "https://londonlatindance.co.uk",
    },
    {
        "name": "Bachata Sensual Miami",
        "email": "dance@bachatasensualmiami.com",
        "city": "Miami",
        "latitude": 25.7825,
        "longitude": -80.2095,
        "description": "Discover the sensual art of Bachata at Miami's dedicated Bachata studio. From Dominican roots to modern Sensual Bachata, our expert instructors will guide you through every body movement and connection technique.",
        "address": "789 Collins Ave, Miami Beach, FL 33140",
        "phone": "+1 (305) 555-0987",
        "website": "https://bachatasensualmiami.com",
    },
    {
        "name": "Swing City Berlin",
        "email": "info@swingcityberlin.de",
        "city": "Berlin",
        "latitude": 52.4934,
        "longitude": 13.4234,
        "description": "Berlin's home for West Coast Swing, Lindy Hop, and Charleston. Step back in time with our vintage-inspired dance nights while learning from internationally acclaimed swing instructors. Live bands every Friday!",
        "address": "Kreuzbergstraße 78, 10965 Berlin, Germany",
        "phone": "+49 30 555 0321",
        "website": "https://swingcityberlin.de",
    },
]

# User Profiles Data
USERS_DATA = [
    {"name": "Sofia Rodriguez", "gender": "female", "city": "Miami", "lat": 25.7617, "lon": -80.1918, "role": "follow", "dances": [{"category": "salsa", "subcategory": "on2", "level": "advanced"}, {"category": "bachata", "subcategory": "sensual", "level": "intermediate"}], "bio": "Professional Salsa dancer & instructor. 8 years experience. Love social dancing and meeting new partners! 💃"},
    {"name": "Marcus Johnson", "gender": "male", "city": "Miami", "lat": 25.7750, "lon": -80.2000, "role": "lead", "dances": [{"category": "salsa", "subcategory": "on1", "level": "advanced"}, {"category": "bachata", "subcategory": "dominicana", "level": "advanced"}], "bio": "Dance is life! Competition dancer turned social dancer. Always looking for new dance partners to practice with."},
    {"name": "Elena Petrova", "gender": "female", "city": "Berlin", "lat": 52.5200, "lon": 13.4050, "role": "follow", "dances": [{"category": "tango", "subcategory": "argentine", "level": "professional"}, {"category": "salsa", "subcategory": "cuban", "level": "intermediate"}], "bio": "Tango is my passion! Originally from Moscow, now dancing in Berlin. Love milongas and meeting new tangueros."},
    {"name": "David Chen", "gender": "male", "city": "London", "lat": 51.5074, "lon": -0.1278, "role": "lead", "dances": [{"category": "salsa", "subcategory": "on2", "level": "intermediate"}, {"category": "other", "subcategory": "kizomba", "level": "beginner"}], "bio": "Software engineer by day, dancer by night. New to Kizomba and loving it! Looking for patient dance partners."},
    {"name": "Isabella Martinez", "gender": "female", "city": "Miami", "lat": 25.7900, "lon": -80.1800, "role": "both", "dances": [{"category": "bachata", "subcategory": "sensual", "level": "professional"}, {"category": "salsa", "subcategory": "on1", "level": "advanced"}], "bio": "Bachata world championship finalist 2024. Teaching & performing. Lead or follow - I do both! 🏆"},
    {"name": "James Wilson", "gender": "male", "city": "Berlin", "lat": 52.4934, "lon": 13.4234, "role": "lead", "dances": [{"category": "swing", "subcategory": "west_coast", "level": "advanced"}, {"category": "swing", "subcategory": "lindy_hop", "level": "intermediate"}], "bio": "Swing dancer and vintage music enthusiast. Love the energy of social dances!"},
    {"name": "Mia Thompson", "gender": "female", "city": "London", "lat": 51.5100, "lon": -0.1300, "role": "follow", "dances": [{"category": "salsa", "subcategory": "on1", "level": "intermediate"}, {"category": "bachata", "subcategory": "traditional", "level": "beginner"}], "bio": "Dance newbie here! Started 6 months ago and already addicted. Patient leads appreciated! 😊"},
    {"name": "Carlos Ramirez", "gender": "male", "city": "Miami", "lat": 25.7650, "lon": -80.1950, "role": "lead", "dances": [{"category": "salsa", "subcategory": "cuban", "level": "professional"}, {"category": "salsa", "subcategory": "on2", "level": "professional"}], "bio": "Cuban-born dancer. Teaching for 15 years. Love sharing my culture through dance! 🇨🇺"},
    {"name": "Anna Schmidt", "gender": "female", "city": "Berlin", "lat": 52.5100, "lon": 13.3900, "role": "follow", "dances": [{"category": "tango", "subcategory": "milonga", "level": "advanced"}, {"category": "tango", "subcategory": "nuevo", "level": "intermediate"}], "bio": "Milonga queen! Nothing beats the feeling of a perfect tango embrace."},
    {"name": "Michael Brown", "gender": "male", "city": "London", "lat": 51.5200, "lon": -0.1150, "role": "both", "dances": [{"category": "other", "subcategory": "kizomba", "level": "advanced"}, {"category": "other", "subcategory": "brazilian_zouk", "level": "intermediate"}], "bio": "Kizomba & Zouk specialist. Love the connection these dances create. Also teach beginners!"},
    {"name": "Lucia Fernandez", "gender": "female", "city": "Miami", "lat": 25.7700, "lon": -80.2100, "role": "follow", "dances": [{"category": "bachata", "subcategory": "dominicana", "level": "advanced"}, {"category": "salsa", "subcategory": "cali", "level": "intermediate"}], "bio": "Dominican roots, Miami vibes! Bachata flows through my veins. Let's dance! 🌴"},
    {"name": "Thomas Weber", "gender": "male", "city": "Berlin", "lat": 52.5050, "lon": 13.4150, "role": "lead", "dances": [{"category": "tango", "subcategory": "argentine", "level": "advanced"}, {"category": "other", "subcategory": "ballroom", "level": "professional"}], "bio": "Classical training meets Argentine passion. Ballroom champion turned tango lover."},
    {"name": "Emma Davis", "gender": "female", "city": "London", "lat": 51.4950, "lon": -0.1400, "role": "both", "dances": [{"category": "swing", "subcategory": "charleston", "level": "intermediate"}, {"category": "swing", "subcategory": "lindy_hop", "level": "beginner"}], "bio": "Vintage enthusiast! Love the 1920s style and music. Learning to Charleston my way through life!"},
    {"name": "Ricardo Silva", "gender": "male", "city": "Miami", "lat": 25.7550, "lon": -80.1850, "role": "lead", "dances": [{"category": "other", "subcategory": "brazilian_zouk", "level": "professional"}, {"category": "other", "subcategory": "kizomba", "level": "advanced"}], "bio": "Brazilian dancer spreading Zouk love in Miami! Weekly classes at the beach. 🏖️"},
    {"name": "Sophie Martin", "gender": "female", "city": "Berlin", "lat": 52.4850, "lon": 13.4300, "role": "follow", "dances": [{"category": "swing", "subcategory": "west_coast", "level": "intermediate"}, {"category": "salsa", "subcategory": "on1", "level": "beginner"}], "bio": "French girl in Berlin. West Coast Swing is my happy place. Also exploring Salsa!"},
]

# Dance Nights / Social Events Data
DANCE_NIGHTS_DATA = [
    # Miami Events
    {"title": "Friday Night Salsa Social", "city": "Miami", "lat": 25.7617, "lon": -80.1918, "dance_types": ["salsa", "bachata"], "venue": "Club Tropicana", "description": "Miami's hottest Friday night salsa party! Two rooms - Salsa On2 in the main room, Bachata in the lounge. Beginner lesson at 9pm, social dancing until 2am. $15 cover includes one drink.", "price": "$15"},
    {"title": "Bachata Sensual Saturdays", "city": "Miami", "lat": 25.7825, "lon": -80.2095, "dance_types": ["bachata"], "venue": "Bachata Sensual Miami Studio", "description": "The ultimate Bachata experience! Sensual Bachata all night with Miami's best DJs. Workshops at 8pm, social dancing 10pm-3am. Air conditioned with premium sound system.", "price": "$20"},
    {"title": "Latin Fusion Sunday Funday", "city": "Miami", "lat": 25.7700, "lon": -80.1900, "dance_types": ["salsa", "bachata", "kizomba"], "venue": "Ocean Drive Rooftop", "description": "Sunset dancing on the rooftop! Mix of Salsa, Bachata & Kizomba with stunning ocean views. Free salsa lesson at 6pm. Dress code: summer elegant.", "price": "$10"},
    {"title": "Cuban Salsa & Timba Night", "city": "Miami", "lat": 25.7550, "lon": -80.1850, "dance_types": ["salsa"], "venue": "Little Havana Cultural Center", "description": "Authentic Cuban music and dancing! Live band playing traditional Son and Timba. Rueda de Casino at 10pm. Cuban food and mojitos available.", "price": "$12"},
    
    # Berlin Events  
    {"title": "Milonga del Centro", "city": "Berlin", "lat": 52.5200, "lon": 13.4050, "dance_types": ["tango"], "venue": "Berlin Tango Haus", "description": "Traditional milonga in the heart of Berlin. Strict tango codes observed. Cortinas, tandas, and cabeceo. Thursday practica at 7pm, milonga 9pm-1am.", "price": "€10"},
    {"title": "Swing & Jazz Evening", "city": "Berlin", "lat": 52.4934, "lon": 13.4234, "dance_types": ["swing"], "venue": "Swing City Berlin", "description": "Live jazz band! West Coast Swing, Lindy Hop, and Charleston. Vintage dress encouraged but not required. Free beginner lesson at 8pm.", "price": "€12"},
    {"title": "Kizomba Connection", "city": "Berlin", "lat": 52.5100, "lon": 13.4100, "dance_types": ["kizomba"], "venue": "Urban Dance Studio", "description": "Berlin's premier Kizomba event. Authentic Kizomba and Urban Kiz. Guest DJs from Lisbon. Workshops during the day, party at night.", "price": "€15"},
    {"title": "Tango Nuevo Experience", "city": "Berlin", "lat": 52.5050, "lon": 13.4150, "dance_types": ["tango"], "venue": "Kreuzberg Arts Center", "description": "Modern tango for modern dancers. Electronic tango music, contemporary choreography welcome. Open floor, no strict codes. Experimental and fun!", "price": "€8"},
    
    # London Events
    {"title": "London Salsa Congress Pre-Party", "city": "London", "lat": 51.5074, "lon": -0.1278, "dance_types": ["salsa", "bachata"], "venue": "London Latin Dance Co.", "description": "Get ready for the Congress! Three floors of dancing - On1, On2, and Bachata. International DJs, performances, and special guests. The biggest Latin party in London!", "price": "£20"},
    {"title": "West End Bachata Nights", "city": "London", "lat": 51.5100, "lon": -0.1250, "dance_types": ["bachata"], "venue": "Soho Dance Hall", "description": "Sensual Bachata in the heart of London's West End. Top UK Bachata DJs spinning the latest hits. Beginner-friendly with free lesson at 8:30pm.", "price": "£12"},
    {"title": "Zouk & Kizomba Fusion", "city": "London", "lat": 51.5000, "lon": -0.1350, "dance_types": ["kizomba", "zouk"], "venue": "Camden Dance Studio", "description": "Where Kizomba meets Brazilian Zouk! Two rooms, two vibes. Chill Kizomba lounge and energetic Zouk main floor. Monthly guest artists.", "price": "£15"},
    {"title": "Tango Under the Stars", "city": "London", "lat": 51.5150, "lon": -0.1200, "dance_types": ["tango"], "venue": "Rooftop Garden Venue", "description": "Summer special! Open-air milonga on London's most beautiful rooftop. Traditional tandas under the night sky. Smart dress code. Reservation required.", "price": "£18"},
]

# Workshops Data
WORKSHOPS_DATA = [
    {"title": "Salsa Shine & Styling Bootcamp", "city": "Miami", "lat": 25.7617, "lon": -80.1918, "dance_types": ["salsa"], "venue": "Miami Salsa Academy", "instructor": "Carlos Ramirez", "description": "Intensive 3-hour workshop focusing on solo shines, body movement, and styling. Perfect for intermediate dancers wanting to level up their skills. Video recording allowed.", "price": "$45", "level": "intermediate"},
    {"title": "Bachata Sensual Intensive", "city": "Miami", "lat": 25.7825, "lon": -80.2095, "dance_types": ["bachata"], "venue": "Bachata Sensual Miami", "instructor": "Isabella Martinez", "description": "Deep dive into sensual bachata techniques. Body waves, isolations, and musical interpretation. Couples and singles welcome. Rotation guaranteed.", "price": "$50", "level": "intermediate"},
    {"title": "Tango Embrace Workshop", "city": "Berlin", "lat": 52.5200, "lon": 13.4050, "dance_types": ["tango"], "venue": "Berlin Tango Haus", "instructor": "Elena Petrova", "description": "Master the art of the tango embrace. Open vs close embrace, navigating the ronda, and musical phrasing. Essential for milonga success.", "price": "€35", "level": "beginner"},
    {"title": "West Coast Swing Musicality", "city": "Berlin", "lat": 52.4934, "lon": 13.4234, "dance_types": ["swing"], "venue": "Swing City Berlin", "instructor": "James Wilson", "description": "Learn to hear the music like a pro! Blues, contemporary, and classic swing interpretation. Anchors, extensions, and musical accents.", "price": "€40", "level": "advanced"},
    {"title": "Kizomba Connection Masterclass", "city": "London", "lat": 51.5074, "lon": -0.1278, "dance_types": ["kizomba"], "venue": "London Latin Dance Co.", "instructor": "Michael Brown", "description": "Building true connection in Kizomba. Ginga fundamentals, saidas, and leading/following techniques. Small groups for personal attention.", "price": "£35", "level": "beginner"},
    {"title": "Ladies Styling for Latin Dances", "city": "London", "lat": 51.5100, "lon": -0.1250, "dance_types": ["salsa", "bachata"], "venue": "Soho Dance Hall", "instructor": "Sofia Rodriguez", "description": "Embrace your feminine energy! Arm styling, hip movement, and floorwork for Salsa and Bachata. All levels welcome. Heels optional.", "price": "£40", "level": "all"},
]

# School Classes Templates
SCHOOL_CLASSES_DATA = [
    # More detailed class offerings
    {"title": "Absolute Beginners Salsa", "level": "beginner", "schedule": "Monday & Wednesday 7:00-8:00 PM", "price": "$80/month", "description": "Never danced before? Start here! Learn basic steps, timing, and partner connection in a fun, supportive environment. No partner needed."},
    {"title": "Salsa On2 Fundamentals", "level": "beginner", "schedule": "Tuesday & Thursday 7:00-8:00 PM", "price": "$85/month", "description": "Master the New York style! Learn the characteristic 'break on 2' timing that gives this style its smooth, musical feel."},
    {"title": "Intermediate Patterns & Turns", "level": "intermediate", "schedule": "Monday & Wednesday 8:15-9:15 PM", "price": "$95/month", "description": "Ready to level up? Learn complex turn patterns, combinations, and smooth transitions. Prerequisite: 6 months of dancing."},
    {"title": "Advanced Musicality & Styling", "level": "advanced", "schedule": "Tuesday & Thursday 8:15-9:15 PM", "price": "$110/month", "description": "For experienced dancers. Advanced footwork, body isolations, and musical interpretation. Audition required."},
    {"title": "Performance Team Training", "level": "advanced", "schedule": "Saturday 2:00-5:00 PM", "price": "$150/month", "description": "Join our performance team! Choreography, stage presence, and competition preparation. By audition only."},
    {"title": "Private Lessons", "level": "all", "schedule": "By appointment", "price": "$75/hour", "description": "One-on-one instruction tailored to your goals. Wedding choreography, competition prep, or personal development."},
]

# School Announcements Templates
SCHOOL_ANNOUNCEMENTS_DATA = [
    {"title": "🎉 Summer Intensive Registration Open!", "content": "Our famous 2-week Summer Intensive is back! August 15-30. Daily classes, workshops with guest instructors, and graduation showcase. Early bird discount: 20% off until July 1st. Limited spots available - register now!"},
    {"title": "🏆 Congratulations to Our Competition Team!", "content": "Huge congratulations to our performance team for winning 1st place at the Regional Dance Championships! Thank you to all our students and supporters. Celebration party this Saturday - everyone welcome!"},
    {"title": "📅 Schedule Changes for July", "content": "Please note the following schedule changes for July: Beginners class moves to Tuesday/Thursday 6:30 PM. Advanced class now includes live music practice on the last Saturday of each month. Updated schedule on our website."},
    {"title": "🌟 New Instructor Joining Our Team", "content": "We're thrilled to welcome Maria Santos, former Cuban National Champion, to our teaching team! She'll be leading a special Cuban Salsa workshop series starting next month. Don't miss this opportunity!"},
    {"title": "💃 Free Community Dance This Friday", "content": "Join us for a FREE community dance this Friday! Celebrate our 10th anniversary with us. Open bar 8-9pm, social dancing until midnight. Bring friends, bring family, let's dance together!"},
]

# Review templates with more variety
REVIEWS = [
    {"rating": 5, "comment": "Absolutely amazing instructors! I went from complete beginner to dancing confidently at socials in just 3 months. The atmosphere is so welcoming and supportive. Highly recommend!"},
    {"rating": 5, "comment": "Best dance school in the city! The teaching methods are clear and effective. I love how they break down complex moves into simple steps. Worth every penny!"},
    {"rating": 4, "comment": "Great classes and friendly community. The venue is beautiful and clean. Only giving 4 stars because parking can be tricky, but that's not the school's fault!"},
    {"rating": 5, "comment": "Life-changing experience! Met my dance partner here and we've been dancing together for 2 years now. The social events are fantastic for meeting people."},
    {"rating": 4, "comment": "Professional instructors who really care about your progress. Love the weekly social events! Would love to see more advanced workshops offered."},
    {"rating": 5, "comment": "From zero dance experience to performing on stage in 8 months! The performance team program is incredible. Can't recommend this school enough!"},
    {"rating": 5, "comment": "The private lessons here transformed my dancing. My instructor identified exactly what I needed to work on and gave me practical exercises to improve."},
]

# Event comments with more engagement
EVENT_COMMENTS = [
    "Can't wait for this! Who's coming? 💃🕺",
    "Last month's event was incredible. This one is going to be even better! See you all there!",
    "First time attending, any tips for newbies? I'm a bit nervous but excited!",
    "The DJ last time was amazing! Hope they're back! Anyone know the playlist?",
    "Bringing 3 friends this time. We're driving from Orlando! 🚗",
    "Is there a beginner-friendly area? Still learning but love the vibe here!",
    "Best event in the city, hands down! The energy is unmatched 🔥",
    "Who wants to practice some combos before the social starts? I'll be there early!",
    "Just booked my flight for this! Coming all the way from New York!",
    "Anyone need a dance partner? I'm a lead, intermediate level. Let's connect!",
    "The live band last time was 🔥🔥🔥 Are they playing again?",
    "Dress code question - is smart casual okay or should I dress up more?",
]

# Partner seeking announcements / messages
PARTNER_ANNOUNCEMENTS = [
    {"title": "Looking for Bachata Practice Partner", "content": "Hi everyone! I'm an intermediate follow looking for a lead to practice Bachata sensual with. Available Tuesday and Thursday evenings in Miami Beach area. I can also help beginners with basics. DM me!"},
    {"title": "Seeking Tango Partner for Milongas", "content": "Experienced tanguera new to Berlin seeking regular milonga partner. I dance close embrace, traditional style. Looking for someone who respects the codigos and loves classic tango music."},
    {"title": "Competition Partner Wanted", "content": "Advanced salsa lead looking for serious competition partner. Training for World Salsa Championships 2025. Must be committed to 15+ hours practice per week. Based in London."},
    {"title": "Social Dancing Buddy", "content": "Just moved to Miami! Looking for friends to go social dancing with. I dance Salsa On1 (intermediate) and learning Bachata. Not looking for romance, just good dance friends!"},
    {"title": "Kizomba Practice Group", "content": "Starting a weekly Kizomba practice group in Berlin! All levels welcome. We meet Sunday afternoons, work on technique, and help each other improve. Free! Just bring good vibes."},
]

async def clear_database():
    """Clear all collections"""
    print("🗑️  Clearing database...")
    collections = await db.list_collection_names()
    for collection in collections:
        await db[collection].delete_many({})
    print("✅ Database cleared!")

async def create_schools():
    """Create seed schools"""
    print("\n🏫 Creating dance schools...")
    school_ids = []
    
    for i, school_data in enumerate(SCHOOLS_DATA):
        password_hash = pwd_context.hash("DanceSchool2024!")
        school_id = ObjectId()
        
        school = {
            "_id": school_id,
            "name": school_data["name"],
            "email": school_data["email"],
            "password_hash": password_hash,
            "user_type": "school",
            "photo": SCHOOL_IMAGES[i],
            "gallery": [SCHOOL_IMAGES[i], EVENT_IMAGES[i % len(EVENT_IMAGES)], EVENT_IMAGES[(i+1) % len(EVENT_IMAGES)]],
            "bio": school_data["description"],
            "dances": [],
            "dance_role": "both",
            "location": {
                "city": school_data["city"],
                "latitude": school_data["latitude"],
                "longitude": school_data["longitude"],
            },
            "school_name": school_data["name"],
            "school_description": school_data["description"],
            "school_address": school_data["address"],
            "school_phone": school_data["phone"],
            "school_website": school_data["website"],
            "is_verified": True,
            "created_at": datetime.utcnow() - timedelta(days=random.randint(30, 365)),
        }
        
        await db.users.insert_one(school)
        school_ids.append(str(school_id))
        
        # Create classes for each school
        await create_classes_for_school(str(school_id), school_data["name"], school_data["city"])
        
        # Create announcements
        await create_announcements_for_school(str(school_id), school_data["name"])
        
        print(f"   ✅ {school_data['name']} - 6 classes, 5 announcements")
    
    return school_ids

async def create_classes_for_school(school_id: str, school_name: str, city: str):
    """Create 6 classes for a school"""
    dance_types = {
        "Miami Salsa Academy": "salsa",
        "Berlin Tango Haus": "tango", 
        "London Latin Dance Co.": "salsa",
        "Bachata Sensual Miami": "bachata",
        "Swing City Berlin": "swing",
    }
    
    dance_type = dance_types.get(school_name, "salsa")
    
    for template in SCHOOL_CLASSES_DATA:
        school_class = {
            "_id": ObjectId(),
            "school_id": school_id,
            "school_name": school_name,
            "title": f"{dance_type.title()} - {template['title']}",
            "description": template["description"],
            "dance_type": dance_type,
            "level": template["level"],
            "schedule": template["schedule"],
            "price_info": template["price"],
            "max_students": random.randint(15, 25),
            "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 30)),
        }
        
        await db.school_classes.insert_one(school_class)

async def create_announcements_for_school(school_id: str, school_name: str):
    """Create 5 announcements for a school"""
    for announcement in SCHOOL_ANNOUNCEMENTS_DATA:
        doc = {
            "_id": ObjectId(),
            "school_id": school_id,
            "school_name": school_name,
            "title": announcement["title"],
            "content": announcement["content"],
            "created_by_id": school_id,
            "created_by_name": school_name,
            "is_teacher": False,
            "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 30)),
        }
        await db.school_announcements.insert_one(doc)

async def create_reviews_for_schools(school_ids: list, user_ids: list):
    """Create reviews for schools"""
    print("\n⭐ Creating school reviews...")
    
    total_reviews = 0
    for school_id in school_ids:
        num_reviews = random.randint(4, 6)
        reviewers = random.sample(user_ids, min(num_reviews, len(user_ids)))
        
        for i, user_id in enumerate(reviewers):
            user = await db.users.find_one({"_id": ObjectId(user_id)})
            review_template = REVIEWS[i % len(REVIEWS)]
            
            review = {
                "_id": ObjectId(),
                "school_id": school_id,
                "user_id": user_id,
                "user_name": user["name"],
                "user_photo": user.get("photo"),
                "rating": review_template["rating"],
                "comment": review_template["comment"],
                "created_at": datetime.utcnow() - timedelta(days=random.randint(7, 90)),
            }
            
            await db.school_reviews.insert_one(review)
            total_reviews += 1
    
    print(f"   ✅ Created {total_reviews} reviews across all schools")

async def create_users():
    """Create seed users"""
    print("\n👤 Creating user profiles...")
    user_ids = []
    male_img_idx = 0
    female_img_idx = 0
    
    for user_data in USERS_DATA:
        password_hash = pwd_context.hash("Dancer2024!")
        user_id = ObjectId()
        
        # Select appropriate profile image
        if user_data["gender"] == "male":
            photo = PROFILE_IMAGES["male"][male_img_idx % len(PROFILE_IMAGES["male"])]
            male_img_idx += 1
        else:
            photo = PROFILE_IMAGES["female"][female_img_idx % len(PROFILE_IMAGES["female"])]
            female_img_idx += 1
        
        email = user_data["name"].lower().replace(" ", ".") + "@dancebuddy.demo"
        
        user = {
            "_id": user_id,
            "name": user_data["name"],
            "email": email,
            "password_hash": password_hash,
            "user_type": "dancer",
            "photo": photo,
            "gallery": [photo],
            "bio": user_data.get("bio", f"Passionate dancer from {user_data['city']}. Love meeting new dance partners!"),
            "dances": user_data["dances"],
            "dance_role": user_data["role"],
            "location": {
                "city": user_data["city"],
                "latitude": user_data["lat"],
                "longitude": user_data["lon"],
            },
            "created_at": datetime.utcnow() - timedelta(days=random.randint(30, 180)),
        }
        
        await db.users.insert_one(user)
        user_ids.append(str(user_id))
        print(f"   ✅ {user_data['name']} ({user_data['role'].upper()}) - {user_data['city']}")
    
    return user_ids

async def create_dance_nights(user_ids: list, school_ids: list):
    """Create dance night events"""
    print("\n🎉 Creating dance nights & social events...")
    event_ids = []
    
    for i, event_data in enumerate(DANCE_NIGHTS_DATA):
        event_id = ObjectId()
        
        # Random organizer (could be school or user)
        city_schools = [sid for sid, sd in zip(school_ids, SCHOOLS_DATA) if sd["city"] == event_data["city"]]
        city_users = [u["name"].lower().replace(" ", ".") + "@dancebuddy.demo" for u in USERS_DATA if u["city"] == event_data["city"]]
        
        if city_schools and random.random() > 0.3:
            organizer_id = random.choice(city_schools)
            organizer = await db.users.find_one({"_id": ObjectId(organizer_id)})
        else:
            organizer_id = random.choice(user_ids)
            organizer = await db.users.find_one({"_id": ObjectId(organizer_id)})
        
        # Event date: upcoming within next 45 days
        event_date = datetime.utcnow() + timedelta(days=random.randint(1, 45), hours=random.randint(19, 22))
        
        event = {
            "_id": event_id,
            "title": event_data["title"],
            "description": event_data["description"],
            "date_time": event_date,
            "location": event_data["venue"],
            "city": event_data["city"],
            "latitude": event_data["lat"],
            "longitude": event_data["lon"],
            "cover_image": EVENT_IMAGES[i % len(EVENT_IMAGES)],
            "dance_types": event_data["dance_types"],
            "price": event_data.get("price", "Free"),
            "organizer_id": str(organizer["_id"]),
            "organizer_name": organizer["name"],
            "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 14)),
        }
        
        await db.dance_nights.insert_one(event)
        event_ids.append(str(event_id))
        
        # Add attendees (6-12 users)
        await add_event_attendees(str(event_id), user_ids, event_data["city"])
        
        # Add comments (2-4)
        await add_event_comments(str(event_id), user_ids)
        
        print(f"   ✅ {event_data['title']} - {event_data['city']}")
    
    return event_ids

async def create_workshops(user_ids: list):
    """Create workshop events"""
    print("\n📚 Creating workshops...")
    workshop_ids = []
    
    for i, workshop_data in enumerate(WORKSHOPS_DATA):
        workshop_id = ObjectId()
        
        # Find instructor by name
        instructor_email = workshop_data["instructor"].lower().replace(" ", ".") + "@dancebuddy.demo"
        instructor = await db.users.find_one({"email": instructor_email})
        
        if not instructor:
            instructor = await db.users.find_one({"user_type": "dancer"})
        
        # Workshop date: upcoming within next 30 days
        workshop_date = datetime.utcnow() + timedelta(days=random.randint(3, 30), hours=random.randint(10, 15))
        
        workshop = {
            "_id": workshop_id,
            "title": workshop_data["title"],
            "description": workshop_data["description"],
            "date_time": workshop_date,
            "location": workshop_data["venue"],
            "city": workshop_data["city"],
            "latitude": workshop_data["lat"],
            "longitude": workshop_data["lon"],
            "cover_image": EVENT_IMAGES[(i + 5) % len(EVENT_IMAGES)],
            "dance_types": workshop_data["dance_types"],
            "price": workshop_data.get("price", "$40"),
            "level": workshop_data.get("level", "all"),
            "instructor_name": workshop_data["instructor"],
            "organizer_id": str(instructor["_id"]) if instructor else user_ids[0],
            "organizer_name": instructor["name"] if instructor else "Dance Buddy",
            "is_workshop": True,
            "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 7)),
        }
        
        await db.dance_nights.insert_one(workshop)
        workshop_ids.append(str(workshop_id))
        
        # Add attendees (4-8 users)
        await add_event_attendees(str(workshop_id), user_ids, workshop_data["city"], max_attendees=8)
        
        print(f"   ✅ {workshop_data['title']} - {workshop_data['instructor']}")
    
    return workshop_ids

async def add_event_attendees(event_id: str, user_ids: list, city: str = None, max_attendees: int = 12):
    """Add attendees to an event"""
    # Prefer users from same city
    if city:
        city_user_emails = [u["name"].lower().replace(" ", ".") + "@dancebuddy.demo" for u in USERS_DATA if u["city"] == city]
        city_users = []
        for email in city_user_emails:
            user = await db.users.find_one({"email": email})
            if user:
                city_users.append(str(user["_id"]))
        
        # Mix of local and other users
        num_local = min(len(city_users), max_attendees - 2)
        num_other = min(len(user_ids) - num_local, 3)
        
        attendee_ids = random.sample(city_users, num_local) if city_users else []
        other_users = [uid for uid in user_ids if uid not in attendee_ids]
        attendee_ids += random.sample(other_users, min(num_other, len(other_users)))
    else:
        num_attendees = random.randint(6, max_attendees)
        attendee_ids = random.sample(user_ids, min(num_attendees, len(user_ids)))
    
    for user_id in attendee_ids:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        
        attendance = {
            "_id": ObjectId(),
            "event_id": event_id,
            "user_id": user_id,
            "user_name": user["name"],
            "user_photo": user.get("photo"),
            "status": "going",
            "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 7)),
        }
        
        await db.event_attendees.insert_one(attendance)

async def add_event_comments(event_id: str, user_ids: list):
    """Add comments to an event"""
    num_comments = random.randint(2, 4)
    commenters = random.sample(user_ids, min(num_comments, len(user_ids)))
    used_comments = random.sample(EVENT_COMMENTS, min(num_comments, len(EVENT_COMMENTS)))
    
    for i, user_id in enumerate(commenters):
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        
        comment = {
            "_id": ObjectId(),
            "event_id": event_id,
            "user_id": user_id,
            "user_name": user["name"],
            "user_photo": user.get("photo"),
            "comment": used_comments[i],
            "created_at": datetime.utcnow() - timedelta(days=random.randint(0, 5), hours=random.randint(0, 23)),
        }
        
        await db.event_comments.insert_one(comment)

async def create_checkins_for_miami_event(user_ids: list):
    """Create check-ins for Miami event to show Live Dance Request feature"""
    print("\n📍 Creating live check-ins for Miami event...")
    
    # Find the first Miami event
    miami_event = await db.dance_nights.find_one({"city": "Miami"})
    if not miami_event:
        print("   ⚠️ No Miami event found")
        return
    
    event_id = str(miami_event["_id"])
    
    # Get Miami-based users
    miami_users = []
    for user_data in USERS_DATA:
        if user_data["city"] == "Miami":
            email = user_data["name"].lower().replace(" ", ".") + "@dancebuddy.demo"
            user = await db.users.find_one({"email": email})
            if user:
                miami_users.append(user)
    
    # Check in users with different statuses
    statuses = ["available", "available", "maybe", "available", "busy", "available"]
    
    for i, user in enumerate(miami_users[:6]):
        checkin = {
            "_id": ObjectId(),
            "event_id": event_id,
            "user_id": str(user["_id"]),
            "user_name": user["name"],
            "user_photo": user.get("photo"),
            "dance_role": user.get("dance_role", "both"),
            "status": statuses[i % len(statuses)],
            "check_in_time": datetime.utcnow() - timedelta(minutes=random.randint(5, 90)),
            "last_active": datetime.utcnow() - timedelta(minutes=random.randint(0, 10)),
        }
        
        await db.live_event_attendees.insert_one(checkin)
        status_emoji = {"available": "🟢", "maybe": "🟡", "busy": "🔴"}[statuses[i % len(statuses)]]
        print(f"   {status_emoji} {user['name']} checked in ({user.get('dance_role', 'both').upper()})")

async def create_friendships_and_requests(user_ids: list):
    """Create friendships and friend requests"""
    print("\n🤝 Creating friendships & partner connections...")
    
    friendships = 0
    requests = 0
    
    # Create 15 accepted friendships
    pairs_for_friendship = []
    for _ in range(15):
        pair = tuple(sorted(random.sample(user_ids, 2)))
        if pair not in pairs_for_friendship:
            pairs_for_friendship.append(pair)
    
    for user1, user2 in pairs_for_friendship:
        existing = await db.friendships.find_one({
            "$or": [
                {"user_id": user1, "friend_id": user2},
                {"user_id": user2, "friend_id": user1}
            ]
        })
        
        if not existing:
            friendship = {
                "_id": ObjectId(),
                "user_id": user1,
                "friend_id": user2,
                "created_at": datetime.utcnow() - timedelta(days=random.randint(7, 60)),
            }
            await db.friendships.insert_one(friendship)
            friendships += 1
    
    # Create 5 pending friend requests ("Let's Dance!" requests)
    for _ in range(5):
        from_user, to_user = random.sample(user_ids, 2)
        
        # Check no existing relationship
        existing = await db.friendships.find_one({
            "$or": [
                {"user_id": from_user, "friend_id": to_user},
                {"user_id": to_user, "friend_id": from_user}
            ]
        })
        existing_request = await db.friend_requests.find_one({
            "$or": [
                {"from_user_id": from_user, "to_user_id": to_user},
                {"from_user_id": to_user, "to_user_id": from_user}
            ]
        })
        
        if not existing and not existing_request:
            from_user_doc = await db.users.find_one({"_id": ObjectId(from_user)})
            
            request = {
                "_id": ObjectId(),
                "from_user_id": from_user,
                "from_user_name": from_user_doc["name"],
                "from_user_photo": from_user_doc.get("photo"),
                "to_user_id": to_user,
                "status": "pending",
                "message": "Let's Dance! 💃🕺",
                "created_at": datetime.utcnow() - timedelta(days=random.randint(0, 3)),
            }
            await db.friend_requests.insert_one(request)
            requests += 1
    
    print(f"   ✅ Created {friendships} dance partnerships")
    print(f"   ✅ Created {requests} pending 'Let's Dance!' requests")

async def create_messages(user_ids: list):
    """Create sample messages between dance partners"""
    print("\n💬 Creating sample messages...")
    
    message_templates = [
        ("Hey! Great dancing with you last night! 💃", "Thanks! You too! Same time next week?"),
        ("Are you going to the salsa social on Friday?", "Yes! I'll be there around 9pm. See you on the dance floor!"),
        ("Would you like to practice that new move we learned?", "Absolutely! How about Sunday afternoon?"),
        ("Thanks for the dance tips! Really helped my spins.", "Anytime! Your footwork is looking much better!"),
        ("Looking for a partner for the workshop. Interested?", "I'd love to! Just signed up. Let's do this! 🎉"),
    ]
    
    # Get some friendships to create messages between
    friendships = await db.friendships.find({}).to_list(10)
    
    messages_created = 0
    for friendship in friendships[:5]:
        user1_id = friendship["user_id"]
        user2_id = friendship["friend_id"]
        
        user1 = await db.users.find_one({"_id": ObjectId(user1_id)})
        user2 = await db.users.find_one({"_id": ObjectId(user2_id)})
        
        if not user1 or not user2:
            continue
            
        template = random.choice(message_templates)
        
        # First message
        msg1 = {
            "_id": ObjectId(),
            "sender_id": user1_id,
            "receiver_id": user2_id,
            "content": template[0],
            "read": True,
            "created_at": datetime.utcnow() - timedelta(hours=random.randint(2, 48)),
        }
        await db.messages.insert_one(msg1)
        
        # Reply
        msg2 = {
            "_id": ObjectId(),
            "sender_id": user2_id,
            "receiver_id": user1_id,
            "content": template[1],
            "read": random.choice([True, False]),
            "created_at": datetime.utcnow() - timedelta(hours=random.randint(0, 2)),
        }
        await db.messages.insert_one(msg2)
        messages_created += 2
    
    print(f"   ✅ Created {messages_created} messages between dance partners")

async def create_school_followers(user_ids: list, school_ids: list):
    """Create school followers"""
    print("\n👥 Creating school followers...")
    
    followers_created = 0
    for school_id in school_ids:
        # Each school gets 6-10 followers
        num_followers = random.randint(6, 10)
        followers = random.sample(user_ids, min(num_followers, len(user_ids)))
        
        for user_id in followers:
            follow = {
                "_id": ObjectId(),
                "user_id": user_id,
                "school_id": school_id,
                "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 60)),
            }
            await db.school_followers.insert_one(follow)
            followers_created += 1
    
    print(f"   ✅ Created {followers_created} school followers")

async def create_admin_user():
    """Create admin user for verification approval"""
    print("\n🛡️ Creating admin user...")
    
    password_hash = pwd_context.hash("Admin2024!")
    admin_id = ObjectId()
    
    admin = {
        "_id": admin_id,
        "name": "Admin User",
        "email": "admin@dancebuddy.app",
        "password_hash": password_hash,
        "user_type": "dancer",  # Admin is a dancer user with is_admin flag
        "photo": "https://images.unsplash.com/photo-1633332755192-727a05c4013d?w=400",
        "gallery": [],
        "bio": "Platform Administrator - Ensuring quality dance experiences for everyone!",
        "dances": [
            {"category": "Latin", "subcategory": "Salsa", "level": "advanced"},
            {"category": "Latin", "subcategory": "Bachata", "level": "intermediate"},
        ],
        "dance_role": "both",
        "location": {
            "city": "San Francisco",
            "latitude": 37.7749,
            "longitude": -122.4194,
        },
        "is_admin": True,  # Admin flag
        "is_verified": False,
        "created_at": datetime.utcnow() - timedelta(days=180),
    }
    
    await db.users.insert_one(admin)
    print(f"   ✅ Admin user created: admin@dancebuddy.app")
    return str(admin_id)

async def create_pending_verification_request(school_ids: list):
    """Create a sample pending verification request for demo"""
    print("\n📋 Creating pending verification request...")
    
    # Create a new unverified school for demo
    password_hash = pwd_context.hash("DanceSchool2024!")
    school_id = ObjectId()
    
    unverified_school = {
        "_id": school_id,
        "name": "Salsa Tropical Studio",
        "email": "info@salsatropical.demo",
        "password_hash": password_hash,
        "user_type": "school",
        "photo": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=600",
        "gallery": [],
        "bio": "New studio bringing the heat of Caribbean salsa to downtown!",
        "dances": [{"type": "salsa", "level": "intermediate"}],
        "dance_role": "both",
        "location": {
            "city": "Miami",
            "latitude": 25.7617,
            "longitude": -80.1918,
        },
        "school_name": "Salsa Tropical Studio",
        "school_description": "New studio bringing the heat of Caribbean salsa to downtown!",
        "school_address": "567 Brickell Ave, Miami, FL 33131",
        "school_phone": "+1 (305) 555-0789",
        "school_website": "https://salsatropical.com",
        "is_verified": False,  # Not verified yet
        "verification_status": "pending",
        "created_at": datetime.utcnow() - timedelta(days=7),
    }
    
    await db.users.insert_one(unverified_school)
    
    # Create verification request
    verification_request = {
        "_id": ObjectId(),
        "school_id": str(school_id),
        "school_name": "Salsa Tropical Studio",
        "school_photo": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=600",
        "business_license_image": "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?w=800",  # Sample document image
        "website_url": "https://salsatropical.com",
        "status": "pending",
        "submitted_at": datetime.utcnow() - timedelta(days=2),
        "reviewed_at": None,
        "reviewed_by": None,
        "rejection_reason": None,
    }
    
    await db.verification_requests.insert_one(verification_request)
    print(f"   ✅ Pending verification request created for: Salsa Tropical Studio")

async def main():
    """Main seed function"""
    print("\n" + "="*60)
    print("🌱 DANCE BUDDY - COMPREHENSIVE SEED DATA SCRIPT")
    print("="*60)
    
    # Clear existing data
    await clear_database()
    
    # Create schools with classes & announcements
    school_ids = await create_schools()
    
    # Create users
    user_ids = await create_users()
    
    # Create admin user
    admin_id = await create_admin_user()
    
    # Create pending verification request for demo
    await create_pending_verification_request(school_ids)
    
    # Create reviews for schools
    await create_reviews_for_schools(school_ids, user_ids)
    
    # Create dance nights / social events
    event_ids = await create_dance_nights(user_ids, school_ids)
    
    # Create workshops
    workshop_ids = await create_workshops(user_ids)
    
    # Create check-ins for Miami event (Live Dance Request feature)
    await create_checkins_for_miami_event(user_ids)
    
    # Create friendships and friend requests
    await create_friendships_and_requests(user_ids)
    
    # Create sample messages
    await create_messages(user_ids)
    
    # Create school followers
    await create_school_followers(user_ids, school_ids)
    
    print("\n" + "="*60)
    print("✅ SEED DATA CREATED SUCCESSFULLY!")
    print("="*60)
    
    print("\n📋 LOGIN CREDENTIALS:")
    print("-"*60)
    print("\n🛡️ ADMIN ACCOUNT (for School Verification):")
    print("   Email: admin@dancebuddy.app")
    print("   Password: Admin2024!")
    print("\n🎓 SCHOOL ACCOUNT:")
    print("   Email: info@miamisalsaacademy.com")
    print("   Password: DanceSchool2024!")
    print("\n💃 PRO USER ACCOUNT (Professional Salsa Lead - Miami):")
    print("   Email: carlos.ramirez@dancebuddy.demo")
    print("   Password: Dancer2024!")
    print("\n🕺 PRO USER ACCOUNT (Professional Bachata - Miami):")
    print("   Email: isabella.martinez@dancebuddy.demo")
    print("   Password: Dancer2024!")
    print("\n🌍 BERLIN USER (Tango Professional):")
    print("   Email: elena.petrova@dancebuddy.demo")
    print("   Password: Dancer2024!")
    print("\n🇬🇧 LONDON USER (Kizomba Advanced):")
    print("   Email: michael.brown@dancebuddy.demo")
    print("   Password: Dancer2024!")
    print("-"*60)
    
    # Count data
    users_count = await db.users.count_documents({})
    schools_count = await db.users.count_documents({"user_type": "school"})
    dancers_count = users_count - schools_count
    events_count = await db.dance_nights.count_documents({})
    classes_count = await db.school_classes.count_documents({})
    announcements_count = await db.school_announcements.count_documents({})
    reviews_count = await db.school_reviews.count_documents({})
    comments_count = await db.event_comments.count_documents({})
    checkins_count = await db.live_event_attendees.count_documents({})
    messages_count = await db.messages.count_documents({})
    friendships_count = await db.friendships.count_documents({})
    
    print("\n📊 SUMMARY:")
    print(f"   • {schools_count} Dance Schools (verified, with full profiles)")
    print(f"   • {dancers_count} Dancer Profiles (with photos & skills)")
    print(f"   • {events_count} Events (Dance Nights + Workshops)")
    print(f"   • {classes_count} School Classes")
    print(f"   • {announcements_count} School Announcements")
    print(f"   • {reviews_count} School Reviews")
    print(f"   • {comments_count} Event Comments")
    print(f"   • {checkins_count} Live Check-ins (Miami event)")
    print(f"   • {messages_count} Messages between partners")
    print(f"   • {friendships_count} Dance Partnerships")
    print("\n")

if __name__ == "__main__":
    asyncio.run(main())
