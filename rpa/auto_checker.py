# rpa/auto_checker.py
# ─────────────────────────────────────────────────────────────────────────────
# RPA Orchestration Pipeline
# This module runs the full automated document-verification workflow after a
# student submits an application.  It is invoked in a background thread so the
# HTTP response is not blocked.
#
# Pipeline steps
# ──────────────
#  1. Load the Application record from the DB.
#  2. Verify academic documents (marksheets, TC, etc.) with existing verifier.
#  3. Verify caste / income certificate based on the student's declared category.
#  4. Combine both results into a single JSON report.
#  5. Persist: rpa_verified=1, rpa_result=<json>, and (if docs missing) flag status.
#  6. Send the appropriate automated email via email_sender.
# ─────────────────────────────────────────────────────────────────────────────

import sys
import os
import json
from datetime import datetime

# Make sure sibling modules in rpa/ are importable wherever this is called from
_RPA_DIR = os.path.dirname(os.path.abspath(__file__))
if _RPA_DIR not in sys.path:
    sys.path.insert(0, _RPA_DIR)

# Uploads root (rpa/ → project/ → project/uploads)
_UPLOADS_DIR = os.path.abspath(os.path.join(_RPA_DIR, "..", "uploads"))


def _resolve_path(relative_or_absolute: str) -> str:
    """Turn a relative upload path (as stored in DB) into an absolute path."""
    if os.path.isabs(relative_or_absolute):
        return relative_or_absolute
    return os.path.join(_UPLOADS_DIR, relative_or_absolute)


# ─────────────────────────────────────────────
# Caste-specific required documents matrix
# ─────────────────────────────────────────────
CASTE_DOC_REQUIREMENTS = {
    "General":  {"caste_cert": False, "income_cert": False},
    "OBC":      {"caste_cert": True,  "income_cert": False},
    "OBC-NCL":  {"caste_cert": True,  "income_cert": True},
    "SC":       {"caste_cert": True,  "income_cert": False},
    "ST":       {"caste_cert": True,  "income_cert": False},
}

# Keywords expected inside each certificate type
CASTE_CERT_KEYWORDS = {
    "SC":      ["scheduled caste", "s.c.", "sc certificate", "caste certificate", "tehsildar", "district magistrate", "gazetted officer"],
    "ST":      ["scheduled tribe", "s.t.", "st certificate", "tribe", "tehsildar", "district magistrate"],
    "OBC":     ["other backward class", "obc", "backward class", "caste certificate"],
    "OBC-NCL": ["other backward class", "obc", "backward class", "caste certificate"],
}
INCOME_CERT_KEYWORDS = [
    "income certificate", "annual income", "non creamy layer", "non-creamy layer",
    "ncl", "8 lakh", "8,00,000", "8 00 000", "below 8", "family income"
]


def _check_keywords(text: str, keywords: list) -> bool:
    t = text.lower()
    return any(kw.lower() in t for kw in keywords)


def verify_caste_documents(caste_category: str, caste_cert_path: str | None,
                            income_cert_path: str | None) -> dict:
    """
    Verify caste / income documents according to the student's declared category.
    Returns a structured report dict.
    """
    reqs = CASTE_DOC_REQUIREMENTS.get(caste_category, CASTE_DOC_REQUIREMENTS["General"])
    result = {
        "category": caste_category,
        "caste_cert_required": reqs["caste_cert"],
        "income_cert_required": reqs["income_cert"],
        "caste_cert_ok": None,
        "income_cert_ok": None,
        "missing_docs": [],
        "issues": [],
        "passed": False,
    }

    # ── Caste certificate check ───────────────────────────────────────────
    if reqs["caste_cert"]:
        if not caste_cert_path:
            result["missing_docs"].append("Caste Certificate")
            result["issues"].append("Caste certificate was not uploaded.")
            result["caste_cert_ok"] = False
        else:
            abs_path = _resolve_path(caste_cert_path)
            if not os.path.exists(abs_path):
                result["missing_docs"].append("Caste Certificate")
                result["issues"].append("Caste certificate file not found on server.")
                result["caste_cert_ok"] = False
            else:
                # Try to read and keyword-match the PDF/text
                from document_reader import read_document
                read_res = read_document(abs_path)
                text = read_res.get("text", "")
                expected_kws = CASTE_CERT_KEYWORDS.get(caste_category, CASTE_CERT_KEYWORDS["OBC"])
                if _check_keywords(text, expected_kws) or read_res.get("type") == "image":
                    # Images are accepted at face value (OCR not implemented)
                    result["caste_cert_ok"] = True
                else:
                    result["caste_cert_ok"] = False
                    result["issues"].append(
                        "Caste certificate does not appear to contain expected keywords. "
                        "Ensure it is an official certificate from the competent authority."
                    )
    else:
        result["caste_cert_ok"] = True   # Not required → auto-pass

    # ── Income / NCL certificate check ───────────────────────────────────
    if reqs["income_cert"]:
        if not income_cert_path:
            result["missing_docs"].append("Income / Non-Creamy Layer Certificate")
            result["issues"].append("Income/NCL certificate was not uploaded.")
            result["income_cert_ok"] = False
        else:
            abs_path = _resolve_path(income_cert_path)
            if not os.path.exists(abs_path):
                result["missing_docs"].append("Income / Non-Creamy Layer Certificate")
                result["issues"].append("Income/NCL certificate file not found on server.")
                result["income_cert_ok"] = False
            else:
                from document_reader import read_document
                read_res = read_document(abs_path)
                text = read_res.get("text", "")
                if _check_keywords(text, INCOME_CERT_KEYWORDS) or read_res.get("type") == "image":
                    result["income_cert_ok"] = True
                else:
                    result["income_cert_ok"] = False
                    result["issues"].append(
                        "Income/NCL certificate does not contain expected keywords. "
                        "Ensure the certificate states 'Non-Creamy Layer' or annual family income."
                    )
    else:
        result["income_cert_ok"] = True   # Not required → auto-pass

    result["passed"] = (result["caste_cert_ok"] is not False) and (result["income_cert_ok"] is not False)
    return result


# ─────────────────────────────────────────────
# Main RPA Orchestration
# ─────────────────────────────────────────────

def run_full_rpa_check(application_id: int, db_session_factory):
    """
    Full RPA pipeline — meant to be called in a background thread.

    Parameters
    ----------
    application_id   : int   – DB primary key of the application
    db_session_factory : callable that returns a new SQLAlchemy Session
    """
    print(f"\n[RPA] ══════════════════════════════════════════")
    print(f"[RPA] Starting full verification for Application #{application_id}")
    print(f"[RPA] Timestamp: {datetime.utcnow().isoformat()}")
    print(f"[RPA] ══════════════════════════════════════════")

    db = db_session_factory()
    try:
        # ── 1. Load application ──────────────────────────────────────────
        from models import Application, User
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            print(f"[RPA] ❌ Application #{application_id} not found in DB.")
            return

        student = db.query(User).filter(User.id == app.student_id).first()
        student_email = student.email if student else None
        student_name  = student.name  if student else "Student"

        print(f"[RPA] Student : {student_name} ({student_email})")
        print(f"[RPA] Category: {app.caste_category}")
        print(f"[RPA] Course  : {app.course}")

        # ── 2. Verify academic documents ────────────────────────────────
        print(f"\n[RPA] Step 2 — Verifying academic documents...")
        academic_result = {"overall_passed": False, "summary": "No academic documents found.", "documents": []}
        if app.documents:
            # Resolve absolute paths for each stored relative path
            doc_paths = [_resolve_path(p.strip()) for p in app.documents.split(",") if p.strip()]
            from verifier import verify_application_documents
            academic_result = verify_application_documents(",".join(doc_paths))
        print(f"[RPA] Academic docs → {'✅ PASSED' if academic_result['overall_passed'] else '❌ FAILED'}")
        print(f"[RPA] {academic_result['summary']}")

        # ── 3. Verify caste / income documents ─────────────────────────
        print(f"\n[RPA] Step 3 — Verifying caste/income documents...")
        caste_result = verify_caste_documents(
            caste_category  = app.caste_category or "General",
            caste_cert_path = app.caste_cert_path,
            income_cert_path= app.income_cert_path,
        )
        print(f"[RPA] Caste docs → {'✅ PASSED' if caste_result['passed'] else '❌ FAILED'}")
        if caste_result["issues"]:
            for iss in caste_result["issues"]:
                print(f"[RPA]   ⚠️  {iss}")

        # ── 4. Build combined report ─────────────────────────────────────
        all_missing = caste_result["missing_docs"][:]
        all_ok = academic_result["overall_passed"] and caste_result["passed"]

        report = {
            "run_at": datetime.utcnow().isoformat(),
            "overall_passed": all_ok,
            "academic": {
                "passed": academic_result["overall_passed"],
                "summary": academic_result["summary"],
                "total_docs": academic_result.get("total_docs", 0),
                "passed_docs": academic_result.get("passed_docs", 0),
                "documents": academic_result.get("documents", []),
            },
            "caste": caste_result,
            "missing_docs": all_missing,
        }

        # ── 5. Persist results to DB ─────────────────────────────────────
        print(f"\n[RPA] Step 5 — Persisting verification results to DB...")
        app.rpa_verified = 1
        app.rpa_result   = json.dumps(report)

        # If caste docs are missing, flag status for admin attention
        if not caste_result["passed"] and app.status == "Pending":
            app.status = "Docs Incomplete"
            print(f"[RPA] ⚠️  Status updated to 'Docs Incomplete'")

        db.commit()
        print(f"[RPA] ✅ DB updated successfully.")

        # ── 6. Send automated email ──────────────────────────────────────
        if student_email:
            print(f"\n[RPA] Step 6 — Sending automated email to {student_email}...")
            from email_sender import (
                send_application_received,
                send_documents_required_email,
            )
            if all_missing:
                send_documents_required_email(
                    student_email, student_name,
                    application_id, app.course,
                    all_missing, caste_result["issues"]
                )
                print(f"[RPA] 📧 'Documents Required' email sent — missing: {all_missing}")
            else:
                send_application_received(student_email, student_name, application_id, app.course)
                print(f"[RPA] 📧 'Application Received' confirmation email sent.")
        else:
            print(f"[RPA] ⚠️  No student email — skipping email step.")

    except Exception as exc:
        print(f"[RPA] ❌ Pipeline error: {exc}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
        print(f"\n[RPA] Pipeline finished for Application #{application_id}")
        print(f"[RPA] ══════════════════════════════════════════\n")
