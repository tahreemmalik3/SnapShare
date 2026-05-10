import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Header
from app import schemas
from app.cosmos_db import create_comment, get_comments_for_photo, get_user_by_id
from app.services.azure_services import analyze_sentiment, get_overall_sentiment
from app.auth import decode_token

router = APIRouter(prefix="/comments", tags=["Comments"])


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


@router.post("/", status_code=201)
def add_comment(payload: schemas.CommentCreate, authorization: str = Header(None)):
    user = get_current_user(authorization)

    sentiments = analyze_sentiment([payload.text])
    sentiment = sentiments[0] if sentiments else "neutral"

    comment = {
        "id": str(uuid.uuid4()),
        "photo_id": payload.photo_id,
        "user_id": user["id"],
        "user_email": user["email"],
        "text": payload.text,
        "sentiment": sentiment,
        "created_at": datetime.utcnow().isoformat()
    }
    created = create_comment(comment)
    return created


@router.get("/")
def get_comments(photo_id: str, authorization: str = Header(None)):
    get_current_user(authorization)
    comments = get_comments_for_photo(photo_id)
    overall = get_overall_sentiment([c.get("sentiment", "neutral") for c in comments])
    return {"comments": comments, "overall_sentiment": overall}