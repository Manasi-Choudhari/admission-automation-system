# 🎓 Student Admission Automation System
### Full-Stack Project: FastAPI + SQLite + Python RPA + HTML/CSS/JS

---

## 📁 Project Structure

```
/project
├── /frontend
│   ├── index.html        ← Home page
│   ├── register.html     ← Student registration
│   ├── login.html        ← Login
│   ├── apply.html        ← Admission application form
│   ├── status.html       ← Track application status
│   ├── admin.html        ← Admin dashboard
│   ├── style.css         ← Global stylesheet
│   └── script.js         ← Shared JS utilities
│
├── /backend
│   ├── main.py           ← FastAPI app entry point
│   ├── database.py       ← SQLAlchemy DB connection
│   ├── models.py         ← ORM table definitions
│   ├── schemas.py        ← Pydantic request/response schemas
│   ├── rpa_trigger.py    ← Bridge to RPA email scripts
│   ├── seed_data.py      ← Creates sample data for testing
│   └── /routes
│       ├── auth.py       ← POST /register, POST /login
│       ├── student.py    ← POST /apply, GET /status/{id}
│       └── admin.py      ← GET/PUT admin routes
│
├── /rpa
│   ├── document_reader.py  ← Read & extract text from PDFs
│   ├── verifier.py         ← Verify document content
│   └── email_sender.py     ← Automated email notifications
│
├── /uploads               ← Uploaded documents stored here
└── requirements.txt       ← Python dependencies
```

---

## ⚙️ Step-by-Step Setup Guide

### Step 1 — Prerequisites

Make sure you have:
- **Python 3.10+** → https://python.org/downloads
- **pip** (comes with Python)
- A modern browser (Chrome, Firefox, Edge)
- (Optional) **Postman** for API testing → https://postman.com

---

### Step 2 — Install Dependencies

Open a terminal in the `/project` root folder:

```bash
# Create a virtual environment (recommended)
python -m venv venv

# Activate it:
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

---

### Step 3 — Configure Email (Optional but Recommended)

Open `/rpa/email_sender.py` and update the `EMAIL_CONFIG` section:

```python
EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "youremail@gmail.com",        # ← Your Gmail
    "sender_password": "xxxx xxxx xxxx xxxx",     # ← Gmail App Password
    "sender_name": "Admissions Office",
    "institution_name": "Bright Future University"
}
```

**How to get a Gmail App Password:**
1. Go to myaccount.google.com → Security
2. Enable 2-Step Verification
3. Search "App Passwords" → Generate one for "Mail"
4. Paste the 16-character password above

> **Note:** If you skip this step, the system still works — emails are just logged to the console instead of being sent.

---

### Step 4 — Run the Backend Server

```bash
# Navigate to the backend folder
cd project/backend

# Start the FastAPI server
uvicorn main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

The database file (`admissions.db`) is created automatically on first run.

---

### Step 5 — Seed Sample Data (Optional)

With the server running, open a **new terminal**:

```bash
cd project/backend
python seed_data.py
```

This creates:
- **Admin:** admin@bfu.edu / admin123
- **Student 1:** rahul@student.com / pass123 (Pending application)
- **Student 2:** priya@student.com / pass123 (Approved application)
- **Student 3:** aman@student.com / pass123 (Rejected application)

---

### Step 6 — Open the Frontend

Simply open the HTML files in your browser:

```
project/frontend/index.html   ← Open this in Chrome/Firefox
```

Or use the VS Code **Live Server** extension for auto-reload.

> **Important:** The frontend is configured to call `http://localhost:8000`.
> If your server runs on a different port, update `API_BASE` in `script.js`.

---

## 🌐 API Endpoints Reference

Base URL: `http://localhost:8000`

Interactive docs: **http://localhost:8000/docs** (Swagger UI)

### Auth Routes

| Method | Endpoint | Description | Body |
|--------|----------|-------------|------|
| POST | `/auth/register` | Register new user | `{name, email, password, role}` |
| POST | `/auth/login` | Login | `{email, password}` |

### Student Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/student/apply` | Submit application (multipart/form-data) |
| GET | `/student/status/{id}` | Get application by ID |
| GET | `/student/my-application/{student_id}` | Get student's own application |

### Admin Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/applications` | Get all applications |
| GET | `/admin/applications?status_filter=Pending` | Filter by status |
| GET | `/admin/applications/{id}` | Get single application |
| PUT | `/admin/approve/{id}` | Approve application |
| PUT | `/admin/reject/{id}` | Reject application |
| GET | `/admin/stats` | Dashboard statistics |

---

## 🧪 Testing with Postman

### Import these example requests:

**1. Register a Student**
```
POST http://localhost:8000/auth/register
Content-Type: application/json

{
  "name": "Test Student",
  "email": "test@example.com",
  "password": "mypassword",
  "role": "student"
}
```

**2. Login**
```
POST http://localhost:8000/auth/login
Content-Type: application/json

{
  "email": "test@example.com",
  "password": "mypassword"
}
```

**3. Submit Application (Form Data)**
```
POST http://localhost:8000/student/apply
Content-Type: multipart/form-data

student_id: 1
course: B.Tech Computer Science
full_name: Test Student
phone: 9876543210
address: 123 Test Street, Mumbai
documents: [attach a PDF file]
```

**4. Check Application Status**
```
GET http://localhost:8000/student/status/1
```

**5. Get All Applications (Admin)**
```
GET http://localhost:8000/admin/applications
```

**6. Approve Application**
```
PUT http://localhost:8000/admin/approve/1
Content-Type: application/json

{
  "admin_notes": "Strong academic record. Welcome to BFU!"
}
```

**7. Reject Application**
```
PUT http://localhost:8000/admin/reject/1
Content-Type: application/json

{
  "admin_notes": "Insufficient marks. Reapply next cycle."
}
```

---

## 🤖 RPA Scripts — How to Use Standalone

### Document Reader
```bash
cd project/rpa
python document_reader.py
```
Reads PDFs and extracts text content.

### Document Verifier
```bash
cd project/rpa
python verifier.py
```
Checks documents for required keywords (name, marks, etc.)

### Email Sender Test
```bash
cd project/rpa
# Edit TEST_EMAIL in the file first!
python email_sender.py
```
Sends test emails using your configured SMTP settings.

---

## 🔐 Security Notes

| Feature | Implementation |
|---------|---------------|
| Password Storage | bcrypt hashing (never plain text) |
| Auth Token | Base64 encoded user_id:role (demo) |
| CORS | Enabled for all origins (restrict in production) |
| File Uploads | Stored in /uploads with UUID filenames |

**For production, also add:**
- JWT tokens with expiry (use `python-jose`)
- HTTPS (SSL certificate)
- Input sanitization
- Rate limiting
- Proper CORS origins

---

## 🐛 Common Issues & Fixes

**Port already in use:**
```bash
uvicorn main:app --reload --port 8001
# Then update API_BASE in script.js to :8001
```

**ModuleNotFoundError:**
```bash
# Make sure venv is activated and run:
pip install -r requirements.txt
```

**CORS errors in browser:**
- Make sure the FastAPI server is running
- Check that `API_BASE` in `script.js` matches your server port

**Email not sending:**
- Verify Gmail App Password (not your regular password)
- Check that 2FA is enabled on your Gmail account
- The system works without email — check console for logs

**Database errors:**
```bash
# Delete the DB and let it recreate:
rm backend/admissions.db
# Restart the server
```

---

## 📊 Sample Data Overview

After running `seed_data.py`:

| User | Email | Password | Role | App Status |
|------|-------|----------|------|------------|
| Admin Kumar | admin@bfu.edu | admin123 | Admin | — |
| Rahul Sharma | rahul@student.com | pass123 | Student | Pending |
| Priya Patel | priya@student.com | pass123 | Student | Approved |
| Aman Gupta | aman@student.com | pass123 | Student | Rejected |

---

## 🚀 Quick Start Checklist

- [ ] Python 3.10+ installed
- [ ] `pip install -r requirements.txt` completed
- [ ] `cd backend && uvicorn main:app --reload` running
- [ ] `python seed_data.py` executed (optional)
- [ ] `frontend/index.html` opened in browser
- [ ] Tested login with admin@bfu.edu / admin123
- [ ] (Optional) Email configured in `/rpa/email_sender.py`

---

*Built with ❤️ using FastAPI · SQLAlchemy · SQLite · bcrypt · PyPDF2 · smtplib*
