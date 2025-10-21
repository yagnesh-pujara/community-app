from enum import Enum
from typing import Optional, List
from datetime import datetime

class UserRole(str, Enum):
    RESIDENT = "resident"
    GUARD = "guard"
    ADMIN = "admin"
    COMMITTEE = "committee"

class VisitorStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"

class EventType(str, Enum):
    VISITOR_CREATED = "visitor_created"
    VISITOR_APPROVED = "visitor_approved"
    VISITOR_DENIED = "visitor_denied"
    VISITOR_CHECKED_IN = "visitor_checked_in"
    VISITOR_CHECKED_OUT = "visitor_checked_out"
    ROLE_CHANGED = "role_changed"