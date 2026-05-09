from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.dependencies import get_db, get_current_user

router = APIRouter(prefix="/ratings", tags=["Ratings"])


@router.post("/", status_code=200)
def rate_photo(
    payload: schemas.RatingCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Rate a photo 1-5 stars.
    If the user has already rated this photo, their rating is updated.
    """
    if payload.rating < 1 or payload.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5.")

    # Check photo exists
    photo = db.query(models.Photo).filter(models.Photo.id == payload.photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found.")

    # Upsert: update existing rating or create new one
    existing = db.query(models.Rating).filter(
        models.Rating.photo_id == payload.photo_id,
        models.Rating.user_id  == current_user.id
    ).first()

    if existing:
        existing.score = payload.rating
        db.commit()
        message = "Rating updated."
    else:
        rating = models.Rating(
            photo_id = payload.photo_id,
            user_id  = current_user.id,
            score    = payload.rating
        )
        db.add(rating)
        db.commit()
        message = "Rating submitted."

    # Calculate new average
    all_ratings = db.query(models.Rating).filter(models.Rating.photo_id == payload.photo_id).all()
    avg = round(sum(r.score for r in all_ratings) / len(all_ratings), 1)

    return {"message": message, "new_avg_rating": avg}
