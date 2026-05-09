from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# ─── AUTH ────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    role: str  # "creator" or "consumer"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    user_id: str
    email: str

class UserOut(BaseModel):
    id: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

# ─── PHOTOS ──────────────────────────────────────────────────────────────────

class PhotoOut(BaseModel):
    id: str
    title: str
    caption: Optional[str] = ""
    location: Optional[str] = ""
    people: Optional[str] = ""
    tags: Optional[List[str]] = []
    image_url: str
    owner_id: str
    owner_email: Optional[str] = ""
    avg_rating: Optional[float] = 0.0
    comment_count: Optional[int] = 0
    user_rating: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

# ─── COMMENTS ────────────────────────────────────────────────────────────────

class CommentCreate(BaseModel):
    photo_id: str
    text: str

class CommentOut(BaseModel):
    id: str
    photo_id: str
    user_id: str
    user_email: Optional[str] = ""
    text: str
    sentiment: Optional[str] = "neutral"
    created_at: datetime

    class Config:
        from_attributes = True

class CommentsResponse(BaseModel):
    comments: List[CommentOut]
    overall_sentiment: str

# ─── RATINGS ─────────────────────────────────────────────────────────────────

class RatingCreate(BaseModel):
    photo_id: str
    rating: int  # 1-5
