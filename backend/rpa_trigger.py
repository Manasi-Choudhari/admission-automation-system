# rpa_trigger.py - Bridge between FastAPI routes and RPA scripts
# Imported by routes to trigger automated emails and the document-check pipeline

import sys
import os
import threading

# Add rpa directory to path so we can import from it
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../rpa"))

try:
    from email_sender import (
        send_application_received,
        send_approval_email,
        send_rejection_email,
        send_documents_required_email,
    )
    RPA_AVAILABLE = True
except ImportError:
    RPA_AVAILABLE = False
    print("[RPA] email_sender not available - emails will be logged only")


# ─────────────────────────────────────────────
# Simple email triggers (called by admin routes)
# ─────────────────────────────────────────────

def trigger_application_received(email: str, name: str, app_id: int, course: str):
    """Trigger 'application received' email."""
    if RPA_AVAILABLE:
        send_application_received(email, name, app_id, course)
    else:
        print(f"[RPA LOG] Application received email → {email} | App ID: {app_id} | Course: {course}")


def trigger_approval_email(email: str, name: str, app_id: int, course: str):
    """Trigger approval email."""
    if RPA_AVAILABLE:
        send_approval_email(email, name, app_id, course)
    else:
        print(f"[RPA LOG] Approval email → {email} | App ID: {app_id} | Course: {course}")


def trigger_rejection_email(email: str, name: str, app_id: int, course: str, reason: str):
    """Trigger rejection email."""
    if RPA_AVAILABLE:
        send_rejection_email(email, name, app_id, course, reason)
    else:
        print(f"[RPA LOG] Rejection email → {email} | App ID: {app_id} | Course: {course}")


# ─────────────────────────────────────────────
# Full RPA Document Verification Pipeline
# Runs in a background thread — non-blocking
# ─────────────────────────────────────────────

def trigger_rpa_document_check(application_id: int, db_session_factory):
    """
    Launch the full RPA verification pipeline in a background thread.
    
    Parameters
    ----------
    application_id    : int      – DB primary key of the newly submitted application
    db_session_factory: callable – called inside the thread to get a fresh DB session
                                   (pass `database.SessionLocal` from main.py context)
    """
    def _run():
        try:
            # Import here so the thread has its own import context
            rpa_dir = os.path.join(os.path.dirname(__file__), "../rpa")
            if rpa_dir not in sys.path:
                sys.path.insert(0, rpa_dir)
            from auto_checker import run_full_rpa_check
            run_full_rpa_check(application_id, db_session_factory)
        except Exception as exc:
            print(f"[RPA] Background thread error for App #{application_id}: {exc}")
            import traceback
            traceback.print_exc()

    thread = threading.Thread(target=_run, name=f"rpa-check-{application_id}", daemon=True)
    thread.start()
    print(f"[RPA] 🚀 Background verification thread started for Application #{application_id}")
