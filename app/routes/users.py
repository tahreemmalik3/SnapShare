import uuid
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from app.auth import hash_password, verify_password, create_access_token
from app.cosmos_db import get_user_by_email, get_user_by_id, create_user

router = APIRouter(prefix="/users", tags=["Users"])

class UserRegister(BaseModel):
    email: str
    password: str
    role: str = "consumer"

class UserLogin(BaseModel):
    email: str
    password: str

@router.post("/register", status_code=201)
def register(payload: UserRegister):
    if payload.role == "creator":
        raise HTTPException(status_code=403, detail="Creator accounts require admin approval.")
    existing = get_user_by_email(payload.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")
    user = {
        "id": str(uuid.uuid4()),
        "email": payload.email,
        "hashed_password": hash_password(payload.password),
        "role": payload.role
    }
    created = create_user(user)
    return {"id": created["id"], "email": created["email"], "role": created["role"]}

@router.post("/login")
def login(payload: UserLogin):
    user = get_user_by_email(payload.email)
    if not user or not verify_password(payload.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    token = create_access_token({"sub": user["id"], "role": user["role"]})
    return {"access_token": token, "token_type": "bearer",
            "role": user["role"], "user_id": user["id"], "email": user["email"]}

@router.get("/me")
def get_me(authorization: str = Header(None)):
    from app.dependencies import get_current_user
    user = get_current_user(authorization)
    return {"id": user["id"], "email": user["email"], "role": user["role"]}

@router.post("/admin/create-creator", status_code=201)
def create_creator(payload: UserRegister):
    existing = get_user_by_email(payload.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")
    user = {
        "id": str(uuid.uuid4()),
        "email": payload.email,
        "hashed_password": hash_password(payload.password),
        "role": "creator"
    }
    created = create_user(user)
    return {"id": created["id"], "email": created["email"], "role": created["role"]}
