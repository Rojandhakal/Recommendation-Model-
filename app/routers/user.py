from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.schemas import UserResponse

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT USER_GUID FROM USERS WHERE STATUS='active'")).fetchall()
    return [{"user_guid": r[0]} for r in rows]
