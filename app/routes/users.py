from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.auth import hash_password, verify_password, create_access_token
from app.dependencies import get_db, get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/register", response_model=schemas.UserOut, status_code=201)
def register(payload: schemas.UserRegister, db: Session = Depends(get_db)):
    """Register a new consumer user. Creator accounts are created by admins only."""
    # Block creator self-registration
    if payload.role == "creator":
        raise HTTPException(status_code=403, detail="Creator accounts require admin approval.")

    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")

    user = models.User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=schemas.Token)
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    """Login and receive a JWT token."""
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_access_token({"sub": user.id, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.id,
        "email": user.email
    }


@router.get("/me", response_model=schemas.UserOut)
def get_me(current_user: models.User = Depends(get_current_user)):
    """Get the currently authenticated user's profile."""
    return current_user


# ─── ADMIN: Create creator account ───────────────────────────────────────────
@router.post("/admin/create-creator", response_model=schemas.UserOut, status_code=201)
def create_creator(payload: schemas.UserRegister, db: Session = Depends(get_db)):
    """
    Admin-only endpoint to create creator accounts.
    In production, protect this with an admin secret header.
    """
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")

    user = models.User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role="creator"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user