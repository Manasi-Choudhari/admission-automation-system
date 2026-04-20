# rpa/verifier.py
# Verifies uploaded documents contain required information

import os
import re
from document_reader import read_all_documents


# Keywords that should be present in valid academic documents
REQUIRED_KEYWORDS = {
    "name_keywords": ["name", "student", "applicant"],
    "marks_keywords": ["marks", "grade", "score", "percentage", "%", "gpa"],
    "id_keywords": ["id", "roll", "registration", "student id"],
    "date_keywords": ["date", "year", "dob", "born"]
}

# Minimum document text length (characters) to consider it readable
MIN_TEXT_LENGTH = 20


def check_keywords(text: str, keywords: list) -> bool:
    """Check if any keyword from the list is present in text (case-insensitive)."""
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


def verify_document(file_path: str, doc_text: str) -> dict:
    """
    Verify a single document for required content.
    Returns a verification result dict.
    """
    result = {
        "file": file_path,
        "is_readable": len(doc_text.strip()) >= MIN_TEXT_LENGTH,
        "has_name": False,
        "has_marks": False,
        "has_id": False,
        "has_date": False,
        "passed": False,
        "issues": []
    }

    if not result["is_readable"]:
        result["issues"].append("Document text too short or unreadable (possibly scanned image).")
        return result

    # Check for each category of keywords
    result["has_name"] = check_keywords(doc_text, REQUIRED_KEYWORDS["name_keywords"])
    result["has_marks"] = check_keywords(doc_text, REQUIRED_KEYWORDS["marks_keywords"])
    result["has_id"] = check_keywords(doc_text, REQUIRED_KEYWORDS["id_keywords"])
    result["has_date"] = check_keywords(doc_text, REQUIRED_KEYWORDS["date_keywords"])

    # Collect issues
    if not result["has_name"]:
        result["issues"].append("No student name found in document.")
    if not result["has_marks"]:
        result["issues"].append("No marks/grades found in document.")

    # Pass condition: must have name + marks (id and date are optional but nice to have)
    result["passed"] = result["has_name"] and result["has_marks"]

    return result


def verify_application_documents(document_paths_str: str) -> dict:
    """
    Verify all documents for an application.
    document_paths_str: comma-separated string of file paths (from DB).
    
    Returns overall verification result with per-document details.
    """
    # Parse comma-separated paths
    paths = [p.strip() for p in document_paths_str.split(",") if p.strip()]

    if not paths:
        return {
            "overall_passed": False,
            "total_docs": 0,
            "passed_docs": 0,
            "documents": [],
            "summary": "No documents found for verification."
        }

    # Read all documents
    print(f"[Verifier] Reading {len(paths)} document(s)...")
    read_results = read_all_documents(paths)

    # Verify each document
    verification_results = []
    passed_count = 0

    for read_result in read_results:
        if read_result["success"]:
            doc_verification = verify_document(
                read_result["file"],
                read_result.get("text", "")
            )
        else:
            doc_verification = {
                "file": read_result["file"],
                "is_readable": False,
                "passed": False,
                "issues": [read_result.get("error", "Could not read file.")],
                "has_name": False,
                "has_marks": False,
                "has_id": False,
                "has_date": False
            }

        if doc_verification["passed"]:
            passed_count += 1

        verification_results.append(doc_verification)
        status_icon = "✅" if doc_verification["passed"] else "❌"
        print(f"[Verifier] {status_icon} {read_result['file']}")
        if doc_verification["issues"]:
            for issue in doc_verification["issues"]:
                print(f"           ⚠️  {issue}")

    # Overall: at least one document must pass
    overall_passed = passed_count > 0

    return {
        "overall_passed": overall_passed,
        "total_docs": len(paths),
        "passed_docs": passed_count,
        "documents": verification_results,
        "summary": (
            f"Verification passed: {passed_count}/{len(paths)} documents verified successfully."
            if overall_passed
            else f"Verification failed: None of the {len(paths)} document(s) met requirements."
        )
    }


def check_file_exists(file_path: str) -> bool:
    """Simple check if a file exists on disk."""
    return os.path.isfile(file_path)


def validate_file_presence(document_paths_str: str) -> dict:
    """Check that all document files actually exist on disk."""
    paths = [p.strip() for p in document_paths_str.split(",") if p.strip()]
    results = {}
    for path in paths:
        results[path] = check_file_exists(path)
    all_present = all(results.values())
    return {
        "all_present": all_present,
        "file_status": results
    }


# ─────────────────────────────────────────────
# Standalone test
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import json

    # Create a mock document for testing
    test_file = "test_marksheet.txt"
    with open(test_file, "w") as f:
        f.write("""
        Certificate of Marks
        Student Name: Rahul Sharma
        Student ID: 2024-CS-001
        Marks Obtained: 425/500 (85%)
        Grade: A+
        Date of Issue: 2024-05-15
        """)

    print("=== Verifier Test ===")
    result = verify_application_documents(test_file)
    print(json.dumps(result, indent=2))

    os.remove(test_file)
