# models.py - SQLAlchemy ORM models (database table definitions)

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    """
    Users table - stores both students and admins.
    role field distinguishes between 'student' and 'admin'.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(200), nullable=False)   # Hashed with bcrypt
    role = Column(String(20), default="student")      # 'student' or 'admin'
    created_at = Column(DateTime, default=datetime.utcnow)

    # One user can have many applications
    applications = relationship("Application", back_populates="student")


class Application(Base):
    """
    Applications table - stores student admission applications.
    status field tracks the admission progress.
    """
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course = Column(String(100), nullable=False)
    full_name = Column(String(100), nullable=False)
    phone = Column(String(20))
    address = Column(Text)
    documents = Column(Text)          # Comma-separated file paths (academic docs)
    status = Column(String(20), default="Pending")   # Pending / Approved / Rejected
    admin_notes = Column(Text, default="")            # Admin can add notes
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ── Caste & Income Details ──────────────────────────────────────────────
    # Category: General / OBC / OBC-NCL / SC / ST
    caste_category = Column(String(30), default="General")
    # Annual family income range, e.g. "Below 1 Lakh", "1-3 Lakh", etc.
    annual_income = Column(String(50), nullable=True)
    # Relative path to uploaded caste certificate (required for SC/ST/OBC/OBC-NCL)
    caste_cert_path = Column(Text, nullable=True)
    # Relative path to uploaded income or Non-Creamy Layer certificate
    income_cert_path = Column(Text, nullable=True)

    # ── RPA Automation Fields ───────────────────────────────────────────────
    # 0 = not run yet, 1 = pipeline has completed
    rpa_verified = Column(Integer, default=0)
    # JSON-encoded string storing the full RPA verification report
    rpa_result = Column(Text, nullable=True)

    # Relationship back to the user who applied
    student = relationship("User", back_populates="applications")
