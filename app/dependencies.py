from fastapi import HTTPException, Header
from app.auth import decode_token
from app.cosmos_db import get_user_by_id

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

def require_creator(user=None):
    if user["role"] != "creator":
        raise HTTPException(status_code=403, detail="Creator access required")
    return user
