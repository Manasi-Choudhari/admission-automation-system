# schemas.py - Pydantic models for request validation and response serialization

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# ─────────────────────────────────────────────
# USER SCHEMAS
# ─────────────────────────────────────────────

class UserRegister(BaseModel):
    """Schema for user registration request body."""
    name: str
    email: EmailStr
    password: str
    role: Optional[str] = "student"   # Defaults to 'student'


class UserLogin(BaseModel):
    """Schema for user login request body."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for returning user data (never expose password)."""
    id: int
    name: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True   # Allow ORM model → Pydantic conversion


# ─────────────────────────────────────────────
# APPLICATION SCHEMAS
# ─────────────────────────────────────────────

class ApplicationResponse(BaseModel):
    """Schema for returning application data."""
    id: int
    student_id: int
    course: str
    full_name: str
    phone: Optional[str]
    address: Optional[str]
    documents: Optional[str]
    status: str
    admin_notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    # Caste & income details
    caste_category: Optional[str] = "General"
    annual_income: Optional[str] = None
    caste_cert_path: Optional[str] = None
    income_cert_path: Optional[str] = None

    # RPA automation fields
    rpa_verified: Optional[int] = 0
    rpa_result: Optional[str] = None

    class Config:
        from_attributes = True


class ApplicationStatusUpdate(BaseModel):
    """Schema for admin to approve/reject with optional notes."""
    admin_notes: Optional[str] = ""


# ─────────────────────────────────────────────
# GENERIC RESPONSE SCHEMAS
# ─────────────────────────────────────────────

class MessageResponse(BaseModel):
    """Generic success/error message response."""
    message: str
    success: bool = True


class LoginResponse(BaseModel):
    """Response returned after successful login."""
    message: str
    user_id: int
    name: str
    email: str
    role: str
    token: str   # Simple token (user_id:role for demo; use JWT in production)
