from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, visitors, chat, notifications
from app.database import get_supabase

app = FastAPI(
    title="Community Management API",
    description="MyGate-style community management system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(visitors.router)
app.include_router(chat.router)
app.include_router(notifications.router)

@app.get("/")
async def root():
    return {"message": "Community Management API", "status": "running"}

@app.get("/health")
async def health_check():
    try:
        supabase = get_supabase()
        # Try a simple query to check database connection
        result = supabase.table("users").select("count").execute()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

# Events endpoint for audit logs
@app.get("/events")
async def get_events():
    """Get audit log events"""
    supabase = get_supabase()
    result = supabase.table("events").select("*").order("occurred_at", desc=True).limit(50).execute()
    return {"events": result.data}