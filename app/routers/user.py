from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas import User
from app.database import get_db

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.get("/", response_model=list[User])
def list_users(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT id, username FROM USERS")).fetchall()
    return [{"id": r[0], "username": r[1]} for r in rows]
