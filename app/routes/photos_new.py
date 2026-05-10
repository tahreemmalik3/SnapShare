import json
import uuid
import os
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query, Header
from typing import Optional
from app.cosmos_db import (create_photo, get_all_photos, get_photo_by_id,
                            delete_photo, get_ratings_for_photo,
                            get_comments_for_photo, get_user_rating_for_photo)
from app.services.azure_services import upload_to_azure_blob, analyze_image_tags
from app.auth import decode_token
from app.cosmos_db import get_user_by_id

router = APIRouter(prefix="/photos", tags=["Photos"])


def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=403, detail="Not authenticated")
    token = authorization.split(" ")[1]
    try:
        payload = decode_token(token)
        user = get_user_by_id(payload["sub"])
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


def build_photo_out(photo: dict, current_user_id: str = None) -> dict:
    ratings = get_ratings_for_photo(photo["id"])
    avg = round(sum(r["score"] for r in ratings) / len(ratings), 1) if ratings else 0.0
    comments = get_comments_for_photo(photo["id"])
    user_rating = None
    if current_user_id:
        ur = get_user_rating_for_photo(photo["id"], current_user_id)
        user_rating = ur["score"] if ur else None
    tags = photo.get("tags", [])
    if isinstance(tags, str):
        try:
            tags = json.loads(tags)
        except Exception:
            tags = []
    return {
        "id": photo["id"],
        "title": photo.get("title", ""),
        "caption": photo.get("caption", ""),
        "location": photo.get("location", ""),
        "people": photo.get("people", ""),
        "tags": tags,
        "image_url": photo.get("image_url", ""),
        "owner_id": photo.get("owner_id", ""),
        "owner_email": photo.get("owner_email", ""),
        "avg_rating": avg,
        "comment_count": len(comments),
        "user_rating": user_rating,
        "created_at": photo.get("created_at", ""),
    }


@router.post("/upload", status_code=201)
async def upload_photo(
    title: str = Form(...),
    caption: str = Form(""),
    location: str = Form(""),
    people: str = Form(""),
    tags: str = Form("[]"),
    image: UploadFile = File(...),
    authorization: str = Header(None)
):
    user = get_current_user(authorization)
    if user["role"] != "creator":
        raise HTTPException(status_code=403, detail="Creator access required")

    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")

    file_bytes = await image.read()

    # Save locally if Azure not configured
    image_url = upload_to_azure_blob(file_bytes, image.filename, image.content_type)

    # AI tagging
    ai_tags = []
    if "placeholder" not in image_url and "picsum" not in image_url and "localhost" not in image_url:
        ai_tags = analyze_image_tags(image_url)

    try:
        manual_tags = json.loads(tags)
    except Exception:
        manual_tags = []
    all_tags = list(set(manual_tags + ai_tags))

    photo = {
        "id": str(uuid.uuid4()),
        "owner_id": user["id"],
        "owner_email": user["email"],
        "title": title,
        "caption": caption,
        "location": location,
        "people": people,
        "tags": all_tags,
        "image_url": image_url,
        "created_at": datetime.utcnow().isoformat()
    }
    created = create_photo(photo)
    return {"message": "Photo uploaded successfully", "photo_id": created["id"], "image_url": image_url}


@router.get("/")
def get_photos(
    search: Optional[str] = Query(None),
    creator_only: Optional[bool] = Query(False),
    authorization: str = Header(None)
):
    user = get_current_user(authorization)
    owner_id = user["id"] if creator_only and user["role"] == "creator" else None
    photos = get_all_photos(search=search, owner_id=owner_id)
    return [build_photo_out(p, user["id"]) for p in photos]


@router.get("/{photo_id}")
def get_photo(photo_id: str, authorization: str = Header(None)):
    user = get_current_user(authorization)
    photo = get_photo_by_id(photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found.")
    return build_photo_out(photo, user["id"])


@router.delete("/{photo_id}")
def remove_photo(photo_id: str, authorization: str = Header(None)):
    user = get_current_user(authorization)
    if user["role"] != "creator":
        raise HTTPException(status_code=403, detail="Creator access required")
    photo = get_photo_by_id(photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found.")
    if photo["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="You can only delete your own photos.")
    delete_photo(photo_id)
    return {"message": "Photo deleted."}