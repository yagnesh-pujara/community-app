from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.schemas import (
    VisitorCreate, VisitorResponse, VisitorApproval,
    VisitorDenial, VisitorCheckin, VisitorCheckout
)
from app.database import get_supabase
from app.auth import get_current_user
from app.dependencies import get_current_resident, get_current_guard
from app.models import VisitorStatus, EventType
from datetime import datetime
from app.utils.fcm import send_notification
import uuid

router = APIRouter(prefix="/visitors", tags=["Visitors"])


async def log_event(event_type: EventType, actor_user_id: str, subject_id: str, payload: dict = None):
    supabase = get_supabase(True)
    event_data = {
        "type": event_type.value,
        "actor_user_id": actor_user_id,
        "subject_id": subject_id,
        "payload": payload or {},
        "occurred_at": datetime.utcnow().isoformat()
    }
    supabase.table("events").insert(event_data).execute()


@router.post("/", response_model=VisitorResponse)
async def create_visitor(
        visitor: VisitorCreate,
        current_user: dict = Depends(get_current_resident)
):
    print("Creating visitor...")
    supabase = get_supabase(True)


    # Ensure user has a household
    if not current_user.get("household_id"):
        raise HTTPException(status_code=400, detail="User must belong to a household")

    visitor_data = {
        "name": visitor.name,
        "phone": visitor.phone,
        "purpose": visitor.purpose,
        "host_household_id": current_user["household_id"],
        "status": VisitorStatus.PENDING.value,
        "scheduled_time": visitor.scheduled_time.isoformat() if visitor.scheduled_time else None
    }

    result = supabase.table("visitors").insert(visitor_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create visitor")

    created_visitor = result.data[0]

    # Log event
    await log_event(
        EventType.VISITOR_CREATED,
        current_user["id"],
        created_visitor["id"],
        {"visitor_name": visitor.name, "purpose": visitor.purpose}
    )

    # Send notification to guards
    await send_notification(
        "guards",
        "New Visitor",
        f"{visitor.name} is pending approval at {current_user.get('display_name')}'s home"
    )

    return created_visitor


@router.get("/", response_model=List[VisitorResponse])
async def get_visitors(current_user: dict = Depends(get_current_user)):
    print("Getting All visitor...")

    supabase = get_supabase(True)

    # Admins and guards see all visitors
    if any(role in current_user.get("roles", []) for role in ["admin", "guard"]):
        result = supabase.table("visitors").select("*").order("created_at", desc=True).execute()
    else:
        # Residents see only their household visitors
        result = supabase.table("visitors").select("*").eq(
            "host_household_id", current_user.get("household_id")
        ).order("created_at", desc=True).execute()

    return result.data


@router.get("/{visitor_id}", response_model=VisitorResponse)
async def get_visitor(visitor_id: str, current_user: dict = Depends(get_current_user)):
    print("Get a visitor...")

    supabase = get_supabase()

    result = supabase.table("visitors").select("*").eq("id", visitor_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Visitor not found")

    visitor = result.data[0]

    # Check permissions
    is_admin_or_guard = any(role in current_user.get("roles", []) for role in ["admin", "guard"])
    is_host = visitor["host_household_id"] == current_user.get("household_id")

    if not (is_admin_or_guard or is_host):
        raise HTTPException(status_code=403, detail="Not authorized to view this visitor")

    return visitor


@router.post("/approve")
async def approve_visitor(
        approval: VisitorApproval,
        current_user: dict = Depends(get_current_resident)
):
    print("Approving visitor...")

    supabase = get_supabase()

    # Get visitor
    result = supabase.table("visitors").select("*").eq("id", approval.visitor_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Visitor not found")

    visitor = result.data[0]

    # Check if user can approve (must be from same household or admin)
    is_admin = "admin" in current_user.get("roles", [])
    is_host = visitor["host_household_id"] == current_user.get("household_id")

    if not (is_admin or is_host):
        raise HTTPException(status_code=403, detail="Not authorized to approve this visitor")

    # Check current status
    if visitor["status"] != VisitorStatus.PENDING.value:
        raise HTTPException(status_code=400, detail=f"Cannot approve visitor with status {visitor['status']}")

    # Update visitor
    update_data = {
        "status": VisitorStatus.APPROVED.value,
        "approved_by": current_user["id"],
        "approved_at": datetime.utcnow().isoformat()
    }

    result = supabase.table("visitors").update(update_data).eq("id", approval.visitor_id).execute()

    # Log event
    await log_event(
        EventType.VISITOR_APPROVED,
        current_user["id"],
        approval.visitor_id,
        {"visitor_name": visitor["name"]}
    )

    # Notify guards
    await send_notification(
        "guards",
        "Visitor Approved",
        f"{visitor['name']} has been approved for entry"
    )

    return {"message": "Visitor approved successfully", "visitor": result.data[0]}


@router.post("/deny")
async def deny_visitor(
        denial: VisitorDenial,
        current_user: dict = Depends(get_current_resident)
):
    print("Denying visitor...")

    supabase = get_supabase(True)

    # Get visitor
    result = supabase.table("visitors").select("*").eq("id", denial.visitor_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Visitor not found")

    visitor = result.data[0]

    # Check permissions
    is_admin = "admin" in current_user.get("roles", [])
    is_host = visitor["host_household_id"] == current_user.get("household_id")

    if not (is_admin or is_host):
        raise HTTPException(status_code=403, detail="Not authorized to deny this visitor")

    # Check current status
    if visitor["status"] != VisitorStatus.PENDING.value:
        raise HTTPException(status_code=400, detail=f"Cannot deny visitor with status {visitor['status']}")

    # Update visitor
    update_data = {
        "status": VisitorStatus.DENIED.value,
        "approved_by": current_user["id"],
        "approved_at": datetime.utcnow().isoformat()
    }

    result = supabase.table("visitors").update(update_data).eq("id", denial.visitor_id).execute()

    # Log event
    await log_event(
        EventType.VISITOR_DENIED,
        current_user["id"],
        denial.visitor_id,
        {"visitor_name": visitor["name"], "reason": denial.reason}
    )

    # Notify guards
    await send_notification(
        "guards",
        "Visitor Denied",
        f"{visitor['name']} has been denied entry"
    )

    return {"message": "Visitor denied successfully", "visitor": result.data[0]}


@router.post("/checkin")
async def checkin_visitor(
        checkin: VisitorCheckin,
        current_user: dict = Depends(get_current_guard)
):
    print("Check-in visitor...")

    supabase = get_supabase()

    # Get visitor
    result = supabase.table("visitors").select("*").eq("id", checkin.visitor_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Visitor not found")

    visitor = result.data[0]


    # Check current status
    if visitor["status"] != VisitorStatus.APPROVED.value:
        raise HTTPException(status_code=400, detail=f"Cannot check in visitor with status {visitor['status']}")

    # Update visitor
    update_data = {
        "status": VisitorStatus.CHECKED_IN.value,
        "checked_in_at": datetime.utcnow().isoformat()
    }

    result = supabase.table("visitors").update(update_data).eq("id", checkin.visitor_id).execute()

    # Log event
    await log_event(
        EventType.VISITOR_CHECKED_IN,
        current_user["id"],
        checkin.visitor_id,
        {"visitor_name": visitor["name"], "guard": current_user["display_name"]}
    )

    # Notify household
    await send_notification(
        f"household_{visitor['host_household_id']}",
        "Visitor Checked In",
        f"{visitor['name']} has checked in"
    )

    return {"message": "Visitor checked in successfully", "visitor": result.data[0]}


@router.post("/checkout")
async def checkout_visitor(
        checkout: VisitorCheckout,
        current_user: dict = Depends(get_current_guard)
):
    print("Check-out visitor...")

    supabase = get_supabase(True)

    # Get visitor
    result = supabase.table("visitors").select("*").eq("id", checkout.visitor_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Visitor not found")

    visitor = result.data[0]

    # Check current status
    if visitor["status"] != VisitorStatus.CHECKED_IN.value:
        raise HTTPException(status_code=400, detail=f"Cannot check out visitor with status {visitor['status']}")

    # Update visitor
    update_data = {
        "status": VisitorStatus.CHECKED_OUT.value,
        "checked_out_at": datetime.utcnow().isoformat()
    }

    result = supabase.table("visitors").update(update_data).eq("id", checkout.visitor_id).execute()

    # Log event
    await log_event(
        EventType.VISITOR_CHECKED_OUT,
        current_user["id"],
        checkout.visitor_id,
        {"visitor_name": visitor["name"], "guard": current_user["display_name"]}
    )

    # Notify household
    await send_notification(
        f"household_{visitor['host_household_id']}",
        "Visitor Checked Out",
        f"{visitor['name']} has checked out"
    )

    return {"message": "Visitor checked out successfully", "visitor": result.data[0]}

