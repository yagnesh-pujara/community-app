from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas import UserCreate, UserResponse, LoginRequest, Token
from app.database import get_supabase
from app.auth import create_access_token, get_current_user
# from app.auth import get_password_hash, verify_password,
from datetime import timedelta
from app.config import get_settings

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    supabase = get_supabase(service=True)

    # Check if user exists
    existing = supabase.table("users").select("*").eq("email", user.email).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user in Supabase Auth (if using auth)
    # For now, we'll just create in database

    # Hash password
    # hashed_password = get_password_hash(user.password)

    # Create user
    user_data = {
        "email": user.email,
        "display_name": user.display_name,
        "phone": user.phone,
        "household_id": user.household_id,
        "roles": [role.value for role in user.roles],
    }

    result = supabase.table("users").insert(user_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create user")

    # Store hashed password separately (you might want a separate table for this)
    # For simplicity, we're not storing it here, but in production you should

    return result.data[0]


@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest):
    supabase = get_supabase(True)

    # Get user
    result = supabase.table("users").select("*").eq("email", login_data.email).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    user = result.data[0]

    # In production, verify password from secure storage
    # For demo, we'll skip password verification
    # if not verify_password(login_data.password, user["hashed_password"]):
    #     raise HTTPException(status_code=401, detail="Incorrect email or password")

    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user["id"], "roles": user["roles"]},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user
