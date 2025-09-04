from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from app.schemas import SwipeResponse, Swipe
from app.database import get_db
from app.service import recommender
from sqlalchemy import text

router = APIRouter(
    prefix="/swipes",
    tags=["swipes"]
)

def retrain_model_in_background(db: Session):
    recommender.initialize_model(db, force_retrain=True)

@router.post("/", response_model=SwipeResponse)
def record_swipe(
    swipe: Swipe,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    try:
        db.execute(
            text("INSERT INTO SWIPES (user_guid, product_guid, direction) VALUES (:u, :p, :d)"),
            {"u": swipe.user_guid, "p": swipe.product_guid, "d": swipe.direction.value}
        )
        db.commit()
    except Exception as e:
        print("DB ERROR:", e)
        raise HTTPException(status_code=400, detail=str(e))

    recommender.NEW_SWIPES_COUNT += 1
    if recommender.NEW_SWIPES_COUNT >= recommender.RETRAIN_THRESHOLD and background_tasks:
        background_tasks.add_task(retrain_model_in_background, db)
        recommender.NEW_SWIPES_COUNT = 0

    liked_products = [p[0] for p in db.execute(
        text("SELECT product_guid FROM SWIPES WHERE user_guid = :uid AND direction='like'"),
        {"uid": swipe.user_guid}
    ).fetchall()]

    return SwipeResponse(user_guid=swipe.user_guid, liked_products=liked_products)

@router.get("/{user_guid}", response_model=SwipeResponse)
def get_liked_products(user_guid: str, db: Session = Depends(get_db)):
    try:
        liked_products = [p[0] for p in db.execute(
            text("SELECT DISTINCT product_guid FROM SWIPES WHERE user_guid = :uid AND direction='like'"),
            {"uid": user_guid}
        ).fetchall()]
        return SwipeResponse(user_guid=user_guid, liked_products=liked_products)
    except Exception as e:
        print("DB ERROR:", e)
        raise HTTPException(status_code=400, detail=str(e))
