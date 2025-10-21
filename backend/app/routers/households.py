from fastapi import APIRouter, HTTPException, Depends

from app.database import get_supabase
from app.schemas import HouseholdResponse
from app.auth import get_current_user

router = APIRouter(prefix="/households", tags=["HouseHolds"])

@router.post("/", response_model=HouseholdResponse)
async def get_house_holds(
    message: HouseholdResponse,
    current_user: dict = Depends(get_current_user)
):
    try:
        supabase = get_supabase()
        response = supabase.table("households").select("*").execute()
        return response
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))