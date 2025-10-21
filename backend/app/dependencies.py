from fastapi import Depends
from app.auth import get_current_user, has_role
from app.models import UserRole

# Dependency for resident access
async def get_current_resident(current_user: dict = Depends(has_role([UserRole.RESIDENT, UserRole.ADMIN]))):
    return current_user

# Dependency for guard access
async def get_current_guard(current_user: dict = Depends(has_role([UserRole.GUARD, UserRole.ADMIN]))):
    return current_user

# Dependency for admin access
async def get_current_admin(current_user: dict = Depends(has_role([UserRole.ADMIN, UserRole.COMMITTEE]))):
    return current_user