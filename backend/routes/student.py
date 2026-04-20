# routes/student.py - Student routes (apply, check status)

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
import uuid
from datetime import datetime

from database import get_db, SessionLocal
from models import Application, User
from schemas import ApplicationResponse

router = APIRouter(prefix="/student", tags=["Student"])

# Absolute path to the uploads folder (sits alongside /backend and /frontend)
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
UPLOAD_DIR = os.path.abspath(UPLOAD_DIR)
os.makedirs(UPLOAD_DIR, exist_ok=True)


def save_uploaded_file(upload_file: UploadFile, subfolder: str = "") -> str:
    """
    Save an uploaded file to the uploads directory.
    Returns a URL-friendly relative path like: student_1/abc123.pdf
    This path is used to build the URL: http://localhost:8000/uploads/student_1/abc123.pdf
    """
    # Create subfolder inside uploads/
    save_dir = os.path.join(UPLOAD_DIR, subfolder)
    os.makedirs(save_dir, exist_ok=True)

    # Preserve original filename suffix, generate unique name
    original_name = upload_file.filename or "document"
    ext = os.path.splitext(original_name)[1].lower() or ".pdf"
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(save_dir, unique_name)

    # Write file to disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    # Return only the relative path from uploads root (for URL construction)
    # e.g. "student_1/abc123.pdf"  →  served at /uploads/student_1/abc123.pdf
    if subfolder:
        return f"{subfolder}/{unique_name}"
    return unique_name


# ─────────────────────────────────────────────
# Caste categories that require extra documents
# ─────────────────────────────────────────────
RESERVED_CATEGORIES = {"OBC", "OBC-NCL", "SC", "ST"}
NCL_CATEGORIES = {"OBC-NCL"}


@router.post("/apply")
async def submit_application(
    student_id: int = Form(...),
    course: str = Form(...),
    full_name: str = Form(...),
    phone: str = Form(...),
    address: str = Form(...),
    # ── Caste & Income fields ──────────────────────────────────────────
    caste_category: str = Form(default="General"),
    annual_income: Optional[str] = Form(default=None),
    # ── Academic documents (mandatory, multiple) ───────────────────────
    documents: List[UploadFile] = File(...),
    # ── Caste certificate (required for reserved categories) ───────────
    caste_cert: Optional[UploadFile] = File(default=None),
    # ── Income / NCL certificate (required for OBC-NCL) ───────────────
    income_cert: Optional[UploadFile] = File(default=None),
    db: Session = Depends(get_db)
):
    """
    Submit a new admission application with document uploads.
    - Accepts personal form fields, caste/income details, and multiple file uploads
    - Saves all files to /uploads folder
    - Creates application record in DB
    - Triggers background RPA verification pipeline
    """
    # Verify student exists
    student = db.query(User).filter(User.id == student_id, User.role == "student").first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found."
        )

    # Check if student already applied
    existing = db.query(Application).filter(Application.student_id == student_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You already have an application (ID: {existing.id}). Status: {existing.status}"
        )

    # ── Validate caste-specific document requirements ──────────────────
    category = caste_category.strip() if caste_category else "General"

    if category in RESERVED_CATEGORIES and (not caste_cert or not caste_cert.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Caste Certificate is required for {category} category students."
        )

    if category in NCL_CATEGORIES and (not income_cert or not income_cert.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Income / Non-Creamy Layer Certificate is required for OBC-NCL students."
        )

    # ── Save academic documents ────────────────────────────────────────
    saved_paths = []
    for doc in documents:
        if doc.filename:
            path = save_uploaded_file(doc, subfolder=f"student_{student_id}")
            saved_paths.append(path)

    if not saved_paths:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload at least one academic document."
        )

    # ── Save caste certificate ─────────────────────────────────────────
    caste_cert_saved = None
    if caste_cert and caste_cert.filename:
        caste_cert_saved = save_uploaded_file(
            caste_cert, subfolder=f"student_{student_id}/caste"
        )

    # ── Save income / NCL certificate ─────────────────────────────────
    income_cert_saved = None
    if income_cert and income_cert.filename:
        income_cert_saved = save_uploaded_file(
            income_cert, subfolder=f"student_{student_id}/income"
        )

    # ── Create the application record ─────────────────────────────────
    new_application = Application(
        student_id=student_id,
        course=course,
        full_name=full_name,
        phone=phone,
        address=address,
        documents=",".join(saved_paths),
        status="Pending",
        # Caste & income
        caste_category=category,
        annual_income=annual_income,
        caste_cert_path=caste_cert_saved,
        income_cert_path=income_cert_saved,
        # RPA fields start as not-run
        rpa_verified=0,
        rpa_result=None,
    )
    db.add(new_application)
    db.commit()
    db.refresh(new_application)

    application_id = new_application.id

    # ── Trigger RPA background pipeline ───────────────────────────────
    try:
        from rpa_trigger import trigger_rpa_document_check
        trigger_rpa_document_check(application_id, SessionLocal)
    except Exception as e:
        print(f"[RPA] Background pipeline trigger failed (non-critical): {e}")

    return {
        "message": "Application submitted successfully! Our automated system will verify your documents.",
        "application_id": application_id,
        "status": new_application.status,
        "caste_category": category,
        "rpa_pipeline": "started",
        "success": True
    }


@router.get("/status/{application_id}", response_model=ApplicationResponse)
def get_application_status(application_id: int, db: Session = Depends(get_db)):
    """
    Get the status of a specific application by its ID.
    Students can use this to track their admission progress.
    """
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application ID {application_id} not found."
        )
    return application


@router.get("/my-application/{student_id}")
def get_student_application(student_id: int, db: Session = Depends(get_db)):
    """Get a student's own application using their user ID."""
    application = db.query(Application).filter(Application.student_id == student_id).first()
    if not application:
        return {"message": "No application found.", "application": None}

    return {
        "application": {
            "id": application.id,
            "course": application.course,
            "full_name": application.full_name,
            "status": application.status,
            "admin_notes": application.admin_notes,
            "caste_category": application.caste_category,
            "annual_income": application.annual_income,
            "rpa_verified": application.rpa_verified,
            "rpa_result": application.rpa_result,
            "created_at": application.created_at.isoformat(),
            "updated_at": application.updated_at.isoformat()
        }
    }