from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from app.schemas import DeviceTokenCreate
from app.auth import get_current_user
from app.database import get_supabase
from app.utils.fcm import send_notification_to_user, subscribe_to_topic
import logging

router = APIRouter(prefix="/notifications", tags=["Notifications"])
logger = logging.getLogger(__name__)


@router.post("/register-token", status_code=status.HTTP_201_CREATED)
async def register_device_token(
        token_data: DeviceTokenCreate,
        current_user: dict = Depends(get_current_user)
):
    """
    Register a device token for push notifications

    - **token**: FCM device token

    Returns success message
    """
    supabase = get_supabase()

    try:
        # Check if token already exists
        existing = supabase.table("device_tokens").select("*").eq("token", token_data.token).execute()

        if existing.data:
            # Update user_id if different
            if existing.data[0]["user_id"] != current_user["id"]:
                supabase.table("device_tokens").update(
                    {"user_id": current_user["id"]}
                ).eq("token", token_data.token).execute()

                logger.info(f"Updated device token ownership to user {current_user['id']}")
                return {
                    "message": "Device token updated successfully",
                    "token_id": existing.data[0]["id"]
                }

            return {
                "message": "Device token already registered",
                "token_id": existing.data[0]["id"]
            }

        # Insert new token
        token_record = {
            "user_id": current_user["id"],
            "token": token_data.token
        }

        result = supabase.table("device_tokens").insert(token_record).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to register device token"
            )

        logger.info(f"Registered new device token for user {current_user['id']}")

        # Subscribe to user's role-based topics
        user_roles = current_user.get("roles", [])
        for role in user_roles:
            await subscribe_to_topic(current_user["id"], role)

        # Subscribe to household topic if user belongs to a household
        if current_user.get("household_id"):
            await subscribe_to_topic(current_user["id"], f"household_{current_user['household_id']}")

        return {
            "message": "Device token registered successfully",
            "token_id": result.data[0]["id"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering device token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register device token"
        )


@router.delete("/unregister-token/{token}", status_code=status.HTTP_200_OK)
async def unregister_device_token(
        token: str,
        current_user: dict = Depends(get_current_user)
):
    """
    Unregister a device token

    - **token**: FCM device token to remove

    Returns success message
    """
    supabase = get_supabase()

    try:
        # Delete token only if it belongs to current user
        result = supabase.table("device_tokens").delete().eq("token", token).eq(
            "user_id", current_user["id"]
        ).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device token not found or does not belong to current user"
            )

        logger.info(f"Unregistered device token for user {current_user['id']}")

        return {
            "message": "Device token unregistered successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unregistering device token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unregister device token"
        )


@router.get("/tokens", status_code=status.HTTP_200_OK)
async def get_user_tokens(current_user: dict = Depends(get_current_user)):
    """
    Get all device tokens for current user

    Returns list of device tokens
    """
    supabase = get_supabase()

    try:
        result = supabase.table("device_tokens").select("*").eq(
            "user_id", current_user["id"]
        ).execute()

        return {
            "tokens": result.data,
            "count": len(result.data)
        }

    except Exception as e:
        logger.error(f"Error fetching device tokens: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch device tokens"
        )


@router.post("/test-notification", status_code=status.HTTP_200_OK)
async def send_test_notification(
        current_user: dict = Depends(get_current_user)
):
    """
    Send a test notification to current user
    Useful for testing FCM integration

    Returns success message
    """
    try:
        await send_notification_to_user(
            current_user["id"],
            "Test Notification",
            f"Hello {current_user['display_name']}! This is a test notification.",
            {"type": "test", "timestamp": "now"}
        )

        return {
            "message": "Test notification sent (check console logs)",
            "note": "In production, this would send an actual FCM notification"
        }

    except Exception as e:
        logger.error(f"Error sending test notification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test notification"
        )


@router.delete("/tokens/all", status_code=status.HTTP_200_OK)
async def unregister_all_tokens(current_user: dict = Depends(get_current_user)):
    """
    Unregister all device tokens for current user
    Useful when user logs out from all devices

    Returns success message with count of deleted tokens
    """
    supabase = get_supabase()

    try:
        # Get count before deletion
        count_result = supabase.table("device_tokens").select("id").eq(
            "user_id", current_user["id"]
        ).execute()

        token_count = len(count_result.data)

        # Delete all tokens
        supabase.table("device_tokens").delete().eq(
            "user_id", current_user["id"]
        ).execute()

        logger.info(f"Unregistered {token_count} device tokens for user {current_user['id']}")

        return {
            "message": f"Successfully unregistered {token_count} device token(s)",
            "count": token_count
        }

    except Exception as e:
        logger.error(f"Error unregistering all tokens: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unregister device tokens"
        )