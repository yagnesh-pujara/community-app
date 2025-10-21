from openai import OpenAI
from app.config import get_settings
from app.database import get_supabase
from app.models import VisitorStatus, EventType
from app.schemas import ChatResponse
from datetime import datetime
from app.utils.fcm import send_notification, send_notification_to_household
import json
import logging
import re

settings = get_settings()

# Initialize Groq client
client = OpenAI(
    api_key=settings.openai_api_key,  # Use your Groq API key here
    base_url="https://api.groq.com/openai/v1"
)

logger = logging.getLogger(__name__)

# Simplified tools format for Groq
tools = [
    {
        "type": "function",
        "function": {
            "name": "approve_visitor",
            "description": "Approve a pending visitor for entry",
            "parameters": {
                "type": "object",
                "properties": {
                    "visitor_name": {
                        "type": "string",
                        "description": "Name of the visitor to approve"
                    }
                },
                "required": ["visitor_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "deny_visitor",
            "description": "Deny a pending visitor",
            "parameters": {
                "type": "object",
                "properties": {
                    "visitor_name": {
                        "type": "string",
                        "description": "Name of the visitor to deny"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for denial"
                    }
                },
                "required": ["visitor_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "checkin_visitor",
            "description": "Check in an approved visitor",
            "parameters": {
                "type": "object",
                "properties": {
                    "visitor_name": {
                        "type": "string",
                        "description": "Name of the visitor to check in"
                    }
                },
                "required": ["visitor_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "checkout_visitor",
            "description": "Check out a visitor",
            "parameters": {
                "type": "object",
                "properties": {
                    "visitor_name": {
                        "type": "string",
                        "description": "Name of the visitor to check out"
                    }
                },
                "required": ["visitor_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_visitors",
            "description": "List visitors by status",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filter by status: pending, approved, denied, checked_in, checked_out, or all",
                        "enum": ["pending", "approved", "denied", "checked_in", "checked_out", "all"]
                    }
                }
            }
        }
    }
]


async def log_event(event_type: EventType, actor_user_id: str, subject_id: str, payload: dict = None):
    """Log an event to the audit log"""
    supabase = get_supabase()
    event_data = {
        "type": event_type.value,
        "actor_user_id": actor_user_id,
        "subject_id": subject_id,
        "payload": payload or {},
        "timestamp": datetime.utcnow().isoformat()
    }
    try:
        supabase.table("events").insert(event_data).execute()
        logger.info(f"Logged event: {event_type.value} by {actor_user_id}")
    except Exception as e:
        logger.error(f"Failed to log event: {str(e)}")


async def approve_visitor_tool(visitor_name: str, current_user: dict):
    """Approve a visitor by name"""
    supabase = get_supabase(True)

    try:
        if "admin" in current_user.get("roles", []):
            result = supabase.table("visitors").select("*").ilike(
                "name", f"%{visitor_name}%"
            ).eq("status", VisitorStatus.PENDING.value).execute()
        else:
            if not current_user.get("household_id"):
                return {
                    "success": False,
                    "message": "You don't belong to any household"
                }

            result = supabase.table("visitors").select("*").ilike(
                "name", f"%{visitor_name}%"
            ).eq("host_household_id", current_user.get("household_id")).eq(
                "status", VisitorStatus.PENDING.value
            ).execute()

        if not result.data:
            return {
                "success": False,
                "message": f"No pending visitor found with name '{visitor_name}'"
            }

        if len(result.data) > 1:
            names = [v["name"] for v in result.data]
            return {
                "success": False,
                "message": f"Multiple visitors found: {', '.join(names)}. Please be more specific."
            }

        visitor = result.data[0]

        is_admin = "admin" in current_user.get("roles", [])
        is_host = visitor["host_household_id"] == current_user.get("household_id")

        if not (is_admin or is_host):
            return {
                "success": False,
                "message": "You don't have permission to approve this visitor"
            }

        update_data = {
            "status": VisitorStatus.APPROVED.value,
            "approved_by": current_user["id"],
            "approved_at": datetime.utcnow().isoformat()
        }

        supabase.table("visitors").update(update_data).eq("id", visitor["id"]).execute()

        await log_event(
            EventType.VISITOR_APPROVED,
            current_user["id"],
            visitor["id"],
            {"visitor_name": visitor["name"], "approved_by": current_user["display_name"]}
        )

        await send_notification(
            "guards",
            "Visitor Approved",
            f"{visitor['name']} has been approved for entry"
        )

        return {
            "success": True,
            "message": f"Approved '{visitor['name']}' successfully",
            "visitor": {"name": visitor["name"], "status": "approved"}
        }

    except Exception as e:
        logger.error(f"Error in approve_visitor_tool: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}


async def deny_visitor_tool(visitor_name: str, reason: str, current_user: dict):
    """Deny a visitor by name"""
    supabase = get_supabase(True)

    try:
        if "admin" in current_user.get("roles", []):
            result = supabase.table("visitors").select("*").ilike(
                "name", f"%{visitor_name}%"
            ).eq("status", VisitorStatus.PENDING.value).execute()
        else:
            if not current_user.get("household_id"):
                return {"success": False, "message": "You don't belong to any household"}

            result = supabase.table("visitors").select("*").ilike(
                "name", f"%{visitor_name}%"
            ).eq("host_household_id", current_user.get("household_id")).eq(
                "status", VisitorStatus.PENDING.value
            ).execute()

        if not result.data:
            return {"success": False, "message": f"No pending visitor found with name '{visitor_name}'"}

        if len(result.data) > 1:
            names = [v["name"] for v in result.data]
            return {"success": False, "message": f"Multiple visitors found: {', '.join(names)}"}

        visitor = result.data[0]

        is_admin = "admin" in current_user.get("roles", [])
        is_host = visitor["host_household_id"] == current_user.get("household_id")

        if not (is_admin or is_host):
            return {"success": False, "message": "No permission to deny this visitor"}

        update_data = {
            "status": VisitorStatus.DENIED.value,
            "approved_by": current_user["id"],
            "approved_at": datetime.utcnow().isoformat()
        }

        supabase.table("visitors").update(update_data).eq("id", visitor["id"]).execute()

        await log_event(
            EventType.VISITOR_DENIED,
            current_user["id"],
            visitor["id"],
            {"visitor_name": visitor["name"], "reason": reason}
        )

        await send_notification("guards", "Visitor Denied", f"{visitor['name']} denied")

        return {
            "success": True,
            "message": f"Denied '{visitor['name']}'. Reason: {reason}",
            "visitor": {"name": visitor["name"], "status": "denied"}
        }

    except Exception as e:
        logger.error(f"Error in deny_visitor_tool: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}


async def checkin_visitor_tool(visitor_name: str, current_user: dict):
    """Check in a visitor"""
    supabase = get_supabase(True)

    try:
        if not any(role in current_user.get("roles", []) for role in ["guard", "admin"]):
            return {"success": False, "message": "Only guards can check in visitors"}

        result = supabase.table("visitors").select("*").ilike(
            "name", f"%{visitor_name}%"
        ).eq("status", VisitorStatus.APPROVED.value).execute()

        if not result.data:
            return {"success": False, "message": f"No approved visitor found: '{visitor_name}'"}

        if len(result.data) > 1:
            names = [v["name"] for v in result.data]
            return {"success": False, "message": f"Multiple visitors: {', '.join(names)}"}

        visitor = result.data[0]

        update_data = {
            "status": VisitorStatus.CHECKED_IN.value,
            "checked_in_at": datetime.utcnow().isoformat()
        }

        supabase.table("visitors").update(update_data).eq("id", visitor["id"]).execute()

        await log_event(
            EventType.VISITOR_CHECKED_IN,
            current_user["id"],
            visitor["id"],
            {"visitor_name": visitor["name"]}
        )

        await send_notification_to_household(
            visitor["host_household_id"],
            "Visitor Checked In",
            f"{visitor['name']} has checked in"
        )

        return {
            "success": True,
            "message": f"Checked in '{visitor['name']}' successfully",
            "visitor": {"name": visitor["name"], "status": "checked_in"}
        }

    except Exception as e:
        logger.error(f"Error in checkin_visitor_tool: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}


async def checkout_visitor_tool(visitor_name: str, current_user: dict):
    """Check out a visitor"""
    supabase = get_supabase(True)

    try:
        if not any(role in current_user.get("roles", []) for role in ["guard", "admin"]):
            return {"success": False, "message": "Only guards can check out visitors"}

        result = supabase.table("visitors").select("*").ilike(
            "name", f"%{visitor_name}%"
        ).eq("status", VisitorStatus.CHECKED_IN.value).execute()

        if not result.data:
            return {"success": False, "message": f"No checked-in visitor found: '{visitor_name}'"}

        if len(result.data) > 1:
            names = [v["name"] for v in result.data]
            return {"success": False, "message": f"Multiple visitors: {', '.join(names)}"}

        visitor = result.data[0]

        update_data = {
            "status": VisitorStatus.CHECKED_OUT.value,
            "checked_out_at": datetime.utcnow().isoformat()
        }

        supabase.table("visitors").update(update_data).eq("id", visitor["id"]).execute()

        await log_event(
            EventType.VISITOR_CHECKED_OUT,
            current_user["id"],
            visitor["id"],
            {"visitor_name": visitor["name"]}
        )

        await send_notification_to_household(
            visitor["host_household_id"],
            "Visitor Checked Out",
            f"{visitor['name']} has checked out"
        )

        return {
            "success": True,
            "message": f"Checked out '{visitor['name']}' successfully",
            "visitor": {"name": visitor["name"], "status": "checked_out"}
        }

    except Exception as e:
        logger.error(f"Error in checkout_visitor_tool: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}


async def list_visitors_tool(status: str, current_user: dict):
    """List visitors with optional status filter"""
    supabase = get_supabase(True)

    try:
        query = supabase.table("visitors").select("*")

        if "admin" in current_user.get("roles", []) or "guard" in current_user.get("roles", []):
            pass
        else:
            if not current_user.get("household_id"):
                return {"success": False, "message": "You don't belong to any household"}
            query = query.eq("host_household_id", current_user.get("household_id"))

        # Set default status if not provided or invalid
        if not status or status not in ["pending", "approved", "denied", "checked_in", "checked_out", "all"]:
            status = "all"

        if status != "all":
            query = query.eq("status", status)

        result = query.order("created_at", desc=True).limit(50).execute()

        if not result.data:
            status_msg = f" with status '{status}'" if status != "all" else ""
            return {
                "success": True,
                "message": f"No visitors found{status_msg}",
                "count": 0,
                "visitors": []
            }

        # Build detailed visitor list
        visitor_list = []
        visitors_by_status = {}

        for v in result.data:
            v_status = v['status']
            if v_status not in visitors_by_status:
                visitors_by_status[v_status] = []
            visitors_by_status[v_status].append(v)

            # Format visitor info
            visitor_info = f"• {v['name']} - Status: {v['status'].upper()} - Phone: {v['phone']}"
            if v.get('purpose'):
                visitor_info += f" - Purpose: {v['purpose']}"
            visitor_list.append(visitor_info)

        # Build summary message
        summary_parts = []
        for vstatus, vlist in visitors_by_status.items():
            summary_parts.append(f"{len(vlist)} {vstatus}")

        summary_msg = f"Found {len(result.data)} total visitor(s): {', '.join(summary_parts)}"

        return {
            "success": True,
            "message": summary_msg,
            "count": len(result.data),
            "visitors": visitor_list,
            "breakdown": {k: len(v) for k, v in visitors_by_status.items()},
            "data": result.data
        }

    except Exception as e:
        logger.error(f"Error in list_visitors_tool: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}", "count": 0}


async def process_chat_message(message: str, current_user: dict) -> ChatResponse:
    """Process chat message with Groq/LLaMA"""

    supabase = get_supabase()

    try:
        # Get visitor context
        if "admin" in current_user.get("roles", []) or "guard" in current_user.get("roles", []):
            visitors_result = supabase.table("visitors").select("*").order(
                "created_at", desc=True
            ).limit(10).execute()
        else:
            if current_user.get("household_id"):
                visitors_result = supabase.table("visitors").select("*").eq(
                    "host_household_id", current_user.get("household_id")
                ).order("created_at", desc=True).limit(10).execute()
            else:
                visitors_result = None

        visitors_context = "Current visitors:\n"
        if visitors_result and visitors_result.data:
            for v in visitors_result.data:
                visitors_context += f"- {v['name']} ({v['status']}, {v['phone']})\n"
        else:
            visitors_context += "No visitors\n"

        system_message = f"""
        You are a helpful AI assistant for a community gate management system.
        
        CURRENT USER INFORMATION:
        - Name: {current_user.get('display_name')}
        - Role: {', '.join(current_user.get('roles', []))}
        - Household ID: {current_user.get('household_id', 'N/A')}
        
        {visitors_context}
        
        IMPORTANT SECURITY RULES:
        1. NEVER mention or expose any IDs, keys, or technical identifiers in your responses
        2. NEVER show household IDs, user IDs, visitor IDs, or any UUID values
        3. NEVER reveal internal system details or database information
        4. Keep all responses user-friendly and non-technical
        
        IMPORTANT: When the user asks about visitors (e.g., "show pending visitors", "list visitors"), you MUST use the list_visitors function to get the current data. The information above may not be complete.

        
        YOUR CAPABILITIES:
        1. approve_visitor(visitor_name) - Approve a pending visitor
        2. deny_visitor(visitor_name, reason) - Deny a pending visitor  
        3. checkin_visitor(visitor_name) - Check in an approved visitor (guards only)
        4. checkout_visitor(visitor_name) - Check out a checked-in visitor (guards only)
        5. list_visitors(status) - List visitors by status (always use this when asked about visitors)
           - status options: "pending", "approved", "checked_in", "checked_out", "all"
        
        RULES:
        - Residents can only approve/deny visitors for their own household
        - Guards and admins can check in/out any visitor
        - Always use list_visitors function when asked to show, list, or display visitors
        - Be friendly and conversational
        - Never expose technical details, IDs, or system internals
        """

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": message}
        ]

        # Call Groq API with tools - using parallel tool calls disabled
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            tools=tools,
            tool_choice="auto",
            parallel_tool_calls=False,  # Important for Groq
            temperature=0.7,
            max_tokens=1024
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        # No tool calls - just return text
        if not tool_calls:
            return ChatResponse(
                response=response_message.content or "I'm here to help with visitor management.",
                action_taken=None,
                details=None
            )

        # Execute first tool call only
        tool_call = tool_calls[0]
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)

        logger.info(f"Executing: {function_name} with {function_args}")

        # Execute tool
        if function_name == "approve_visitor":
            result = await approve_visitor_tool(function_args.get("visitor_name"), current_user)
        elif function_name == "deny_visitor":
            result = await deny_visitor_tool(
                function_args.get("visitor_name"),
                function_args.get("reason", "No reason"),
                current_user
            )
        elif function_name == "checkin_visitor":
            result = await checkin_visitor_tool(function_args.get("visitor_name"), current_user)
        elif function_name == "checkout_visitor":
            result = await checkout_visitor_tool(function_args.get("visitor_name"), current_user)
        elif function_name == "list_visitors":
            result = await list_visitors_tool(function_args.get("status", "all"), current_user)
        else:
            result = {"success": False, "message": f"Unknown function: {function_name}"}

        # Add function result to messages
        messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": [tool_call]
        })
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "name": function_name,
            "content": json.dumps(result)
        })

        # Get final response
        final_response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.7,
            max_tokens=512
        )

        return ChatResponse(
            response=final_response.choices[0].message.content,
            action_taken=function_name,
            details=result
        )

    except Exception as e:
        logger.error(f"Error in process_chat_message: {str(e)}")
        # Return user-friendly error
        return ChatResponse(
            response=f"I encountered an error: {str(e)}. Please try rephrasing your request.",
            action_taken=None,
            details={"error": str(e)}
        )