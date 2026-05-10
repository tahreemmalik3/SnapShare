import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Header
from app import schemas
from app.cosmos_db import create_or_update_rating, get_ratings_for_photo, get_user_by_id
from app.auth import decode_token

router = APIRouter(prefix="/ratings", tags=["Ratings"])


def get_current_user(authorization: str = None):
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


@router.post("/", status_code=200)
def rate_photo(payload: schemas.RatingCreate, authorization: str = Header(None)):
    user = get_current_user(authorization)

    if payload.rating < 1 or payload.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5.")

    rating_data = {
        "id": str(uuid.uuid4()),
        "photo_id": payload.photo_id,
        "user_id": user["id"],
        "score": payload.rating,
        "created_at": datetime.utcnow().isoformat()
    }
    create_or_update_rating(rating_data)

    all_ratings = get_ratings_for_photo(payload.photo_id)
    avg = round(sum(r["score"] for r in all_ratings) / len(all_ratings), 1)
    return {"message": "Rating submitted.", "new_avg_rating": avg}