import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from app import models, schemas
from app.dependencies import get_db, get_current_user, require_creator
from app.services.azure_services import upload_to_azure_blob, analyze_image_tags

router = APIRouter(prefix="/photos", tags=["Photos"])


def build_photo_out(photo: models.Photo, db: Session, current_user_id: str = None) -> dict:
    """Helper: assemble PhotoOut dict with computed fields."""
    ratings   = db.query(models.Rating).filter(models.Rating.photo_id == photo.id).all()
    avg       = round(sum(r.score for r in ratings) / len(ratings), 1) if ratings else 0.0
    count     = db.query(models.Comment).filter(models.Comment.photo_id == photo.id).count()
    user_rate = None
    if current_user_id:
        ur = db.query(models.Rating).filter(
            models.Rating.photo_id == photo.id,
            models.Rating.user_id  == current_user_id
        ).first()
        user_rate = ur.score if ur else None

    tags = []
    try:
        tags = json.loads(photo.tags) if photo.tags else []
    except Exception:
        pass

    return {
        "id":            photo.id,
        "title":         photo.title,
        "caption":       photo.caption,
        "location":      photo.location,
        "people":        photo.people,
        "tags":          tags,
        "image_url":     photo.image_url,
        "owner_id":      photo.owner_id,
        "owner_email":   photo.owner.email if photo.owner else "",
        "avg_rating":    avg,
        "comment_count": count,
        "user_rating":   user_rate,
        "created_at":    photo.created_at,
    }


# ─── UPLOAD (Creator only) ────────────────────────────────────────────────────

@router.post("/upload", status_code=201)
async def upload_photo(
    title:    str        = Form(...),
    caption:  str        = Form(""),
    location: str        = Form(""),
    people:   str        = Form(""),
    tags:     str        = Form("[]"),   # JSON string from frontend AI analysis
    image:    UploadFile = File(...),
    db:       Session    = Depends(get_db),
    current_user: models.User = Depends(require_creator)
):
    """Upload a photo with metadata. Creator only."""
    # Validate file type
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")

    file_bytes = await image.read()

    # 1. Upload to Azure Blob Storage
    image_url = upload_to_azure_blob(file_bytes, image.filename, image.content_type)

    # 2. Auto-tag with Azure Computer Vision (if URL available)
    ai_tags = []
    if "placeholder" not in image_url:
        ai_tags = analyze_image_tags(image_url)

    # Merge user-provided tags and AI tags
    try:
        manual_tags = json.loads(tags)
    except Exception:
        manual_tags = []
    all_tags = list(set(manual_tags + ai_tags))

    # 3. Save to database
    photo = models.Photo(
        owner_id  = current_user.id,
        title     = title,
        caption   = caption,
        location  = location,
        people    = people,
        tags      = json.dumps(all_tags),
        image_url = image_url,
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)

    return {"message": "Photo uploaded successfully", "photo_id": photo.id, "image_url": image_url}


# ─── GET ALL PHOTOS (with search & filter) ────────────────────────────────────

@router.get("/", response_model=List[dict])
def get_photos(
    search:       Optional[str]  = Query(None),
    creator_only: Optional[bool] = Query(False),
    skip:         int            = Query(0),
    limit:        int            = Query(50),
    db:           Session        = Depends(get_db),
    current_user: models.User    = Depends(get_current_user)
):
    """
    Get all photos. Supports:
    - search: searches title, caption, location, people, tags
    - creator_only: returns only the current user's photos (for creator dashboard)
    """
    query = db.query(models.Photo)

    if creator_only and current_user.role == "creator":
        query = query.filter(models.Photo.owner_id == current_user.id)

    if search:
        term = f"%{search.lower()}%"
        query = query.filter(
            models.Photo.title.ilike(term)    |
            models.Photo.caption.ilike(term)  |
            models.Photo.location.ilike(term) |
            models.Photo.people.ilike(term)   |
            models.Photo.tags.ilike(term)
        )

    photos = query.order_by(models.Photo.created_at.desc()).offset(skip).limit(limit).all()
    return [build_photo_out(p, db, current_user.id) for p in photos]


# ─── GET SINGLE PHOTO ────────────────────────────────────────────────────────

@router.get("/{photo_id}")
def get_photo(
    photo_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get a single photo by ID."""
    photo = db.query(models.Photo).filter(models.Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found.")
    return build_photo_out(photo, db, current_user.id)


# ─── DELETE PHOTO (Creator / owner only) ─────────────────────────────────────

@router.delete("/{photo_id}")
def delete_photo(
    photo_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_creator)
):
    """Delete a photo. Only the owner can delete their own photo."""
    photo = db.query(models.Photo).filter(models.Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found.")
    if photo.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own photos.")
    db.delete(photo)
    db.commit()
    return {"message": "Photo deleted."}
