from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import models, schemas
from app.dependencies import get_db, get_current_user
from app.services.azure_services import analyze_sentiment, get_overall_sentiment

router = APIRouter(prefix="/comments", tags=["Comments"])


@router.post("/", response_model=schemas.CommentOut, status_code=201)
def add_comment(
    payload: schemas.CommentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Add a comment to a photo.
    Azure Text Analytics automatically analyses the sentiment.
    """
    # Check photo exists
    photo = db.query(models.Photo).filter(models.Photo.id == payload.photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found.")

    # Analyse sentiment of the new comment
    sentiments = analyze_sentiment([payload.text])
    sentiment  = sentiments[0] if sentiments else "neutral"

    comment = models.Comment(
        photo_id  = payload.photo_id,
        user_id   = current_user.id,
        text      = payload.text,
        sentiment = sentiment,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    return {
        "id":         comment.id,
        "photo_id":   comment.photo_id,
        "user_id":    comment.user_id,
        "user_email": current_user.email,
        "text":       comment.text,
        "sentiment":  comment.sentiment,
        "created_at": comment.created_at,
    }


@router.get("/", response_model=schemas.CommentsResponse)
def get_comments(
    photo_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get all comments for a photo, plus the overall sentiment score.
    """
    photo = db.query(models.Photo).filter(models.Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found.")

    comments = (
        db.query(models.Comment)
        .filter(models.Comment.photo_id == photo_id)
        .order_by(models.Comment.created_at.asc())
        .all()
    )

    comment_out = []
    for c in comments:
        comment_out.append({
            "id":         c.id,
            "photo_id":   c.photo_id,
            "user_id":    c.user_id,
            "user_email": c.user.email if c.user else "",
            "text":       c.text,
            "sentiment":  c.sentiment,
            "created_at": c.created_at,
        })

    overall = get_overall_sentiment([c.sentiment for c in comments])

    return {"comments": comment_out, "overall_sentiment": overall}
