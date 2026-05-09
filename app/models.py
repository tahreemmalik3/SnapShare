from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id          = Column(String, primary_key=True, default=generate_uuid)
    email       = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role        = Column(String, nullable=False)  # "creator" or "consumer"
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    photos      = relationship("Photo",   back_populates="owner")
    comments    = relationship("Comment", back_populates="user")
    ratings     = relationship("Rating",  back_populates="user")


class Photo(Base):
    __tablename__ = "photos"

    id          = Column(String, primary_key=True, default=generate_uuid)
    owner_id    = Column(String, ForeignKey("users.id"), nullable=False)
    title       = Column(String, nullable=False)
    caption     = Column(Text, default="")
    location    = Column(String, default="")
    people      = Column(String, default="")   # comma-separated names
    tags        = Column(Text, default="")     # JSON array as string
    image_url   = Column(String, nullable=False)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    owner       = relationship("User",    back_populates="photos")
    comments    = relationship("Comment", back_populates="photo", cascade="all, delete")
    ratings     = relationship("Rating",  back_populates="photo", cascade="all, delete")


class Comment(Base):
    __tablename__ = "comments"

    id          = Column(String, primary_key=True, default=generate_uuid)
    photo_id    = Column(String, ForeignKey("photos.id"), nullable=False)
    user_id     = Column(String, ForeignKey("users.id"),  nullable=False)
    text        = Column(Text, nullable=False)
    sentiment   = Column(String, default="neutral")  # positive / negative / neutral
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    photo       = relationship("Photo", back_populates="comments")
    user        = relationship("User",  back_populates="comments")


class Rating(Base):
    __tablename__ = "ratings"

    id          = Column(String, primary_key=True, default=generate_uuid)
    photo_id    = Column(String, ForeignKey("photos.id"), nullable=False)
    user_id     = Column(String, ForeignKey("users.id"),  nullable=False)
    score       = Column(Integer, nullable=False)  # 1-5
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    photo       = relationship("Photo", back_populates="ratings")
    user        = relationship("User",  back_populates="ratings")
