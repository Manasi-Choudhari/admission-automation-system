# main.py - FastAPI Application Entry Point
# Run with: uvicorn main:app --reload

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from database import engine, Base
from routes import auth, student, admin

# ─────────────────────────────────────────────
# Create all database tables on startup
# ─────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ─────────────────────────────────────────────
# Initialize FastAPI app
# ─────────────────────────────────────────────
app = FastAPI(
    title="Student Admission Automation System",
    description="API for automating student admissions with document verification and email notifications.",
    version="1.0.0",
    docs_url="/docs",        # Swagger UI at http://localhost:8000/docs
    redoc_url="/redoc"       # ReDoc UI at http://localhost:8000/redoc
)

# ─────────────────────────────────────────────
# Enable CORS - allows frontend to call this API
# In production, replace "*" with your actual frontend domain
# ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Allow all origins (update in production)
    allow_credentials=True,
    allow_methods=["*"],          # Allow all HTTP methods
    allow_headers=["*"],          # Allow all headers
)

# ─────────────────────────────────────────────
# Serve uploaded files as static files
# ─────────────────────────────────────────────
UPLOAD_DIR = "../uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# ─────────────────────────────────────────────
# Register route modules
# ─────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(student.router)
app.include_router(admin.router)


# ─────────────────────────────────────────────
# Root endpoint
# ─────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "message": "Student Admission Automation System API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health")
def health_check():
    """Health check endpoint to verify the API is running."""
    return {"status": "healthy", "message": "API is running successfully."}
