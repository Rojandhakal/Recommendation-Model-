from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import schemas, crud
from app.database import get_db

router = APIRouter(
    prefix="/swipes",
    tags=["Swipes"]
)

@router.post("/", response_model=schemas.Swipe)
def record_swipe(swipe: schemas.SwipeBase, user_id: int, db: Session = Depends(get_db)):
    return crud.create_swipe(db, swipe, user_id)

@router.get("/")
def get_swipes(user_id: int, db: Session = Depends(get_db)):
    return crud.get_user_swipes(db, user_id)
