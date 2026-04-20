#!/usr/bin/env python3
"""
seed_data.py - Creates sample data for testing the system
Run from the /backend directory: python seed_data.py

Creates:
  - 1 Admin account
  - 3 Student accounts
  - 3 Sample applications
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal, engine, Base
from models import User, Application
import bcrypt
from datetime import datetime

def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def seed():
    # Create all tables first
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("🌱 Seeding database...\n")

    # ── Admin Account ──
    admin = db.query(User).filter(User.email == "admin@bfu.edu").first()
    if not admin:
        admin = User(
            name="Admin Kumar",
            email="admin@bfu.edu",
            password=hash_pw("admin123"),
            role="admin"
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print("✅ Admin created: admin@bfu.edu / admin123")
    else:
        print("⚠️  Admin already exists.")

    # ── Student Accounts ──
    students_data = [
        {"name": "Rahul Sharma", "email": "rahul@student.com", "password": "pass123"},
        {"name": "Priya Patel",  "email": "priya@student.com",  "password": "pass123"},
        {"name": "Aman Gupta",   "email": "aman@student.com",   "password": "pass123"},
    ]

    students = []
    for sd in students_data:
        existing = db.query(User).filter(User.email == sd["email"]).first()
        if not existing:
            s = User(name=sd["name"], email=sd["email"], password=hash_pw(sd["password"]), role="student")
            db.add(s)
            db.commit()
            db.refresh(s)
            students.append(s)
            print(f"✅ Student created: {sd['email']} / {sd['password']}")
        else:
            students.append(existing)
            print(f"⚠️  Student already exists: {sd['email']}")

    # ── Sample Applications ──
    app_data = [
        {"course": "B.Tech Computer Science",   "status": "Pending",  "notes": ""},
        {"course": "MBA Business Analytics",     "status": "Approved", "notes": "Strong academic background. Welcome!"},
        {"course": "B.Tech Electronics Engineering", "status": "Rejected", "notes": "Insufficient marks in Physics. Reapply next cycle."},
    ]

    for i, (student, ad) in enumerate(zip(students, app_data)):
        existing = db.query(Application).filter(Application.student_id == student.id).first()
        if not existing:
            app = Application(
                student_id=student.id,
                course=ad["course"],
                full_name=student.name,
                phone=f"987654321{i}",
                address=f"{i+1}23, Sample Street, Mumbai, Maharashtra - 400001",
                documents="sample_marksheet.pdf,sample_certificate.pdf",
                status=ad["status"],
                admin_notes=ad["notes"]
            )
            db.add(app)
            db.commit()
            db.refresh(app)
            print(f"✅ Application #{app.id} created for {student.name} — Status: {ad['status']}")
        else:
            print(f"⚠️  Application already exists for {student.name}")

    db.close()

    print("\n" + "="*50)
    print("🎉 Seed complete! You can now test with:")
    print("")
    print("  Admin Login:")
    print("    Email:    admin@bfu.edu")
    print("    Password: admin123")
    print("")
    print("  Student Logins:")
    print("    rahul@student.com / pass123 (Pending)")
    print("    priya@student.com / pass123 (Approved)")
    print("    aman@student.com  / pass123 (Rejected)")
    print("="*50)

if __name__ == "__main__":
    seed()
