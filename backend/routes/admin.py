# routes/admin.py - Admin routes (view all applications, approve/reject)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database import get_db
from models import Application, User
from schemas import ApplicationResponse, ApplicationStatusUpdate

router = APIRouter(prefix="/admin", tags=["Admin"])


def get_application_with_student(app: Application, db: Session) -> dict:
    """Helper to build a rich application dict including student info."""
    student = db.query(User).filter(User.id == app.student_id).first()
    return {
        "id": app.id,
        "student_id": app.student_id,
        "student_name": student.name if student else "Unknown",
        "student_email": student.email if student else "Unknown",
        "course": app.course,
        "full_name": app.full_name,
        "phone": app.phone,
        "address": app.address,
        "documents": app.documents,
        "status": app.status,
        "admin_notes": app.admin_notes,
        # Caste & income details
        "caste_category": app.caste_category or "General",
        "annual_income": app.annual_income,
        "caste_cert_path": app.caste_cert_path,
        "income_cert_path": app.income_cert_path,
        # RPA automation fields
        "rpa_verified": app.rpa_verified or 0,
        "rpa_result": app.rpa_result,
        "created_at": app.created_at.isoformat(),
        "updated_at": app.updated_at.isoformat()
    }



@router.get("/applications")
def get_all_applications(
    status_filter: str = None,
    db: Session = Depends(get_db)
):
    """
    Get all applications. Admin can optionally filter by status.
    Query param: ?status_filter=Pending | Approved | Rejected
    """
    query = db.query(Application)
    if status_filter:
        query = query.filter(Application.status == status_filter)

    applications = query.order_by(Application.created_at.desc()).all()

    result = [get_application_with_student(app, db) for app in applications]

    return {
        "total": len(result),
        "applications": result
    }


@router.get("/applications/{application_id}")
def get_single_application(application_id: int, db: Session = Depends(get_db)):
    """Get a single application's full details."""
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found."
        )
    return get_application_with_student(app, db)


@router.put("/approve/{application_id}")
def approve_application(
    application_id: int,
    update_data: ApplicationStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Approve a student's application.
    Admin can optionally add notes explaining the decision.
    Triggers an approval email via RPA.
    """
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found."
        )

    if app.status != "Pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Application is already {app.status}. Cannot modify."
        )

    # Update status
    app.status = "Approved"
    app.admin_notes = update_data.admin_notes or "Congratulations! Your application has been approved."
    app.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(app)

    # Trigger RPA approval email
    try:
        student = db.query(User).filter(User.id == app.student_id).first()
        if student:
            from rpa_trigger import trigger_approval_email
            trigger_approval_email(student.email, student.name, application_id, app.course)
    except Exception as e:
        print(f"[RPA] Approval email failed (non-critical): {e}")

    return {
        "message": f"Application {application_id} approved successfully.",
        "application_id": application_id,
        "status": "Approved",
        "success": True
    }


@router.put("/reject/{application_id}")
def reject_application(
    application_id: int,
    update_data: ApplicationStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Reject a student's application.
    Admin should provide a reason in admin_notes.
    Triggers a rejection email via RPA.
    """
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found."
        )

    if app.status != "Pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Application is already {app.status}. Cannot modify."
        )

    # Update status
    app.status = "Rejected"
    app.admin_notes = update_data.admin_notes or "We regret to inform you that your application was not successful."
    app.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(app)

    # Trigger RPA rejection email
    try:
        student = db.query(User).filter(User.id == app.student_id).first()
        if student:
            from rpa_trigger import trigger_rejection_email
            trigger_rejection_email(student.email, student.name, application_id, app.course, app.admin_notes)
    except Exception as e:
        print(f"[RPA] Rejection email failed (non-critical): {e}")

    return {
        "message": f"Application {application_id} rejected.",
        "application_id": application_id,
        "status": "Rejected",
        "success": True
    }


@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get summary statistics for the admin dashboard."""
    total = db.query(Application).count()
    pending = db.query(Application).filter(Application.status == "Pending").count()
    approved = db.query(Application).filter(Application.status == "Approved").count()
    rejected = db.query(Application).filter(Application.status == "Rejected").count()
    total_students = db.query(User).filter(User.role == "student").count()

    return {
        "total_applications": total,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "total_students": total_students
    }
