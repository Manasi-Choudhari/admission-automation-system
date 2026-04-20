# rpa/document_reader.py
# Reads uploaded PDFs and images, extracts text content for verification

import os
import json
from pathlib import Path

# Try importing PyPDF2 - install with: pip install PyPDF2
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("[WARNING] PyPDF2 not installed. Install with: pip install PyPDF2")


def read_pdf(file_path: str) -> dict:
    """
    Extract text content from a PDF file.
    Returns a dict with page count, extracted text, and metadata.
    """
    result = {
        "file": file_path,
        "type": "pdf",
        "pages": 0,
        "text": "",
        "success": False,
        "error": None
    }

    if not PDF_AVAILABLE:
        result["error"] = "PyPDF2 not installed"
        return result

    if not os.path.exists(file_path):
        result["error"] = f"File not found: {file_path}"
        return result

    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            result["pages"] = len(reader.pages)
            
            # Extract text from all pages
            full_text = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                full_text.append(f"--- Page {i+1} ---\n{page_text}")
            
            result["text"] = "\n".join(full_text)
            result["success"] = True

    except Exception as e:
        result["error"] = str(e)

    return result


def read_text_file(file_path: str) -> dict:
    """Read a plain text file."""
    result = {
        "file": file_path,
        "type": "text",
        "text": "",
        "success": False,
        "error": None
    }
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            result["text"] = f.read()
            result["success"] = True
    except Exception as e:
        result["error"] = str(e)
    return result


def read_document(file_path: str) -> dict:
    """
    Auto-detect file type and extract text accordingly.
    Supports: PDF, TXT
    Images are noted but text extraction requires OCR (not included).
    """
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        return read_pdf(file_path)
    elif ext in [".txt", ".text"]:
        return read_text_file(file_path)
    elif ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp"]:
        return {
            "file": file_path,
            "type": "image",
            "text": "[Image file - OCR not implemented]",
            "success": True,
            "error": None
        }
    else:
        return {
            "file": file_path,
            "type": "unknown",
            "text": "",
            "success": False,
            "error": f"Unsupported file type: {ext}"
        }


def read_all_documents(file_paths: list) -> list:
    """Read multiple documents. file_paths is a list of file path strings."""
    results = []
    for path in file_paths:
        path = path.strip()
        if path:
            result = read_document(path)
            results.append(result)
            print(f"[DocumentReader] Read: {path} → Success: {result['success']}")
    return results


# ─────────────────────────────────────────────
# Standalone test (run this file directly to test)
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=== Document Reader Test ===")
    
    # Create a test PDF for demonstration
    test_txt = "test_document.txt"
    with open(test_txt, "w") as f:
        f.write("Student Name: John Doe\nMarks: 85%\nCourse: Computer Science\nDOB: 2000-01-15")
    
    result = read_document(test_txt)
    print(json.dumps(result, indent=2))
    
    os.remove(test_txt)  # Cleanup
