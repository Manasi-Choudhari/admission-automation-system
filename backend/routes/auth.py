# routes/auth.py - Authentication routes (register & login)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import bcrypt
import base64

from database import get_db
from models import User
from schemas import UserRegister, UserLogin, UserResponse, LoginResponse, MessageResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


def hash_password(plain_password: str) -> str:
    """Hash a plain text password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against its bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


def create_simple_token(user_id: int, role: str) -> str:
    """
    Create a simple token (base64 encoded user_id:role).
    NOTE: In production, use JWT tokens with proper expiry.
    """
    token_data = f"{user_id}:{role}"
    return base64.b64encode(token_data.encode()).decode()


@router.post("/register", response_model=MessageResponse)
def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user (student or admin).
    - Checks if email already exists
    - Hashes the password before storing
    """
    # Check if email already registered
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered. Please login."
        )

    # Create new user with hashed password
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password=hash_password(user_data.password),
        role=user_data.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": f"Account created successfully! Welcome, {new_user.name}.", "success": True}


@router.post("/login", response_model=LoginResponse)
def login_user(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login an existing user.
    - Verifies email exists
    - Checks password against stored hash
    - Returns a simple token for frontend auth
    """
    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No account found with this email."
        )

    # Verify password
    if not verify_password(credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password. Please try again."
        )

    # Generate token
    token = create_simple_token(user.id, user.role)

    return {
        "message": f"Welcome back, {user.name}!",
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "token": token
    }
