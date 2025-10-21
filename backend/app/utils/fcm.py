import httpx
import json
from typing import Optional, List
from app.config import get_settings
from app.database import get_supabase
import logging

settings = get_settings()
logger = logging.getLogger(__name__)


async def send_notification(topic: str, title: str, body: str, data: Optional[dict] = None):
    """
    Send FCM notification to a topic

    Args:
        topic: Topic name (e.g., 'guards', 'household_{id}')
        title: Notification title
        body: Notification body
        data: Optional additional data payload
    """
    # For local development, just log the notification
    # In production, implement actual FCM HTTP v1 API

    logger.info(f"[NOTIFICATION] Topic: {topic}")
    logger.info(f"  Title: {title}")
    logger.info(f"  Body: {body}")
    if data:
        logger.info(f"  Data: {json.dumps(data)}")

    print(f"\n{'=' * 60}")
    print(f"📢 NOTIFICATION")
    print(f"{'=' * 60}")
    print(f"Topic: {topic}")
    print(f"Title: {title}")
    print(f"Body: {body}")
    if data:
        print(f"Data: {json.dumps(data, indent=2)}")
    print(f"{'=' * 60}\n")

    # TODO: Implement actual FCM sending when Firebase is configured
    # Example implementation below:
    """
    if not all([settings.fcm_project_id, settings.fcm_private_key, settings.fcm_client_email]):
        logger.warning("FCM credentials not configured, skipping actual notification")
        return

    try:
        # Get access token
        import google.oauth2.service_account
        import google.auth.transport.requests

        credentials = google.oauth2.service_account.Credentials.from_service_account_info(
            {
                "type": "service_account",
                "project_id": settings.fcm_project_id,
                "private_key": settings.fcm_private_key.replace('\\n', '\n'),
                "client_email": settings.fcm_client_email,
            },
            scopes=["https://www.googleapis.com/auth/firebase.messaging"]
        )

        request = google.auth.transport.requests.Request()
        credentials.refresh(request)
        access_token = credentials.token

        # Prepare FCM message
        fcm_message = {
            "message": {
                "topic": topic,
                "notification": {
                    "title": title,
                    "body": body
                },
                "data": data or {},
                "android": {
                    "priority": "high"
                },
                "apns": {
                    "payload": {
                        "aps": {
                            "sound": "default",
                            "badge": 1
                        }
                    }
                }
            }
        }

        # Send to FCM
        url = f"https://fcm.googleapis.com/v1/projects/{settings.fcm_project_id}/messages:send"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=fcm_message, headers=headers)

        if response.status_code == 200:
            logger.info(f"Notification sent successfully to topic: {topic}")
        else:
            logger.error(f"Failed to send notification: {response.text}")

    except Exception as e:
        logger.error(f"Error sending FCM notification: {str(e)}")
    """


async def send_notification_to_user(user_id: str, title: str, body: str, data: Optional[dict] = None):
    """
    Send notification to specific user by their device tokens

    Args:
        user_id: User UUID
        title: Notification title
        body: Notification body
        data: Optional additional data payload
    """
    supabase = get_supabase()

    try:
        # Get user's device tokens
        result = supabase.table("device_tokens").select("token").eq("user_id", user_id).execute()

        if not result.data:
            logger.info(f"No device tokens found for user {user_id}")
            return

        tokens = [token_record["token"] for token_record in result.data]

        # Log notification for each token
        for token in tokens:
            logger.info(f"[NOTIFICATION] User: {user_id}, Token: {token[:20]}...")
            logger.info(f"  Title: {title}")
            logger.info(f"  Body: {body}")
            if data:
                logger.info(f"  Data: {json.dumps(data)}")

            print(f"\n{'=' * 60}")
            print(f"📱 USER NOTIFICATION")
            print(f"{'=' * 60}")
            print(f"User ID: {user_id}")
            print(f"Device Token: {token[:20]}...")
            print(f"Title: {title}")
            print(f"Body: {body}")
            if data:
                print(f"Data: {json.dumps(data, indent=2)}")
            print(f"{'=' * 60}\n")

        # TODO: Implement actual FCM sending when Firebase is configured
        # Similar to send_notification but using tokens instead of topics
        """
        if not all([settings.fcm_project_id, settings.fcm_private_key, settings.fcm_client_email]):
            logger.warning("FCM credentials not configured, skipping actual notification")
            return

        # Send to each token
        for token in tokens:
            fcm_message = {
                "message": {
                    "token": token,
                    "notification": {
                        "title": title,
                        "body": body
                    },
                    "data": data or {}
                }
            }
            # ... send logic similar to above
        """

    except Exception as e:
        logger.error(f"Error sending notification to user {user_id}: {str(e)}")


async def send_notification_to_household(household_id: str, title: str, body: str, data: Optional[dict] = None):
    """
    Send notification to all members of a household

    Args:
        household_id: Household UUID
        title: Notification title
        body: Notification body
        data: Optional additional data payload
    """
    supabase = get_supabase()

    try:
        # Get all household members
        result = supabase.table("users").select("id").eq("household_id", household_id).execute()

        if not result.data:
            logger.info(f"No users found for household {household_id}")
            return

        # Send notification to each member
        for user in result.data:
            await send_notification_to_user(user["id"], title, body, data)

    except Exception as e:
        logger.error(f"Error sending notification to household {household_id}: {str(e)}")


async def send_notification_to_role(role: str, title: str, body: str, data: Optional[dict] = None):
    """
    Send notification to all users with a specific role

    Args:
        role: Role name (e.g., 'guard', 'admin')
        title: Notification title
        body: Notification body
        data: Optional additional data payload
    """
    supabase = get_supabase()

    try:
        # Get all users with this role
        # Note: In PostgreSQL, we use @> operator to check if array contains value
        result = supabase.table("users").select("id").filter("roles", "cs", f'{{{role}}}').execute()

        if not result.data:
            logger.info(f"No users found with role {role}")
            return

        logger.info(f"Sending notification to {len(result.data)} users with role {role}")

        # Send notification to each user
        for user in result.data:
            await send_notification_to_user(user["id"], title, body, data)

    except Exception as e:
        logger.error(f"Error sending notification to role {role}: {str(e)}")


async def subscribe_to_topic(user_id: str, topic: str):
    """
    Subscribe a user's device tokens to a topic
    This is useful for role-based or household-based topics

    Args:
        user_id: User UUID
        topic: Topic name
    """
    supabase = get_supabase()

    try:
        # Get user's device tokens
        result = supabase.table("device_tokens").select("token").eq("user_id", user_id).execute()

        if not result.data:
            logger.info(f"No device tokens found for user {user_id}")
            return

        tokens = [token_record["token"] for token_record in result.data]

        logger.info(f"Subscribing {len(tokens)} tokens to topic {topic} for user {user_id}")

        # TODO: Implement FCM topic subscription
        # https://firebase.google.com/docs/cloud-messaging/manage-topics

    except Exception as e:
        logger.error(f"Error subscribing user {user_id} to topic {topic}: {str(e)}")

