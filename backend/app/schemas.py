from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from app.models import UserRole, VisitorStatus, EventType


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    display_name: str
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: str
    household_id: Optional[str] = None
    roles: List[UserRole] = [UserRole.RESIDENT]


class UserResponse(UserBase):
    id: str
    household_id: Optional[str]
    roles: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# Household Schemas
class HouseholdCreate(BaseModel):
    flat_no: str
    name: Optional[str] = None


class HouseholdResponse(BaseModel):
    id: str
    flat_no: str
    name: Optional[str]
    members: List[str]
    created_at: datetime


# Visitor Schemas
class VisitorCreate(BaseModel):
    name: str
    phone: str
    purpose: Optional[str] = None
    scheduled_time: Optional[datetime] = None


class VisitorUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    purpose: Optional[str] = None
    scheduled_time: Optional[datetime] = None


class VisitorResponse(BaseModel):
    id: str
    name: str
    phone: str
    purpose: Optional[str]
    host_household_id: str
    status: VisitorStatus
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    checked_in_at: Optional[datetime]
    checked_out_at: Optional[datetime]
    scheduled_time: Optional[datetime]
    created_at: datetime


class VisitorApproval(BaseModel):
    visitor_id: str


class VisitorDenial(BaseModel):
    visitor_id: str
    reason: Optional[str] = None


class VisitorCheckin(BaseModel):
    visitor_id: str


class VisitorCheckout(BaseModel):
    visitor_id: str


# Event Schemas
class EventCreate(BaseModel):
    type: EventType
    actor_user_id: str
    subject_id: Optional[str] = None
    payload: Optional[dict] = None


class EventResponse(BaseModel):
    id: str
    type: str
    actor_user_id: str
    subject_id: Optional[str]
    payload: Optional[dict]
    occurred_at: datetime


# Chat Schemas
class ChatMessage(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    action_taken: Optional[str] = None
    details: Optional[dict] = None


# Device Token Schema
class DeviceTokenCreate(BaseModel):
    token: str