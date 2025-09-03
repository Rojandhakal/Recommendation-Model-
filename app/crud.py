from sqlalchemy.orm import Session
from app import models, schemas
from app.models import SwipeDirection

def create_swipe(db: Session, swipe: schemas.SwipeBase, user_guid: str):
    db_swipe = models.Swipe(
        user_guid=user_guid,
        product_guid=swipe.product_guid,
        direction=SwipeDirection(swipe.direction.value if hasattr(swipe.direction, "value") else swipe.direction)
    )
    db.add(db_swipe)
    db.commit()
    db.refresh(db_swipe)
    return db_swipe

def get_user_swipes(db: Session, user_guid: str):
    return db.query(models.Swipe).filter(models.Swipe.user_guid == user_guid).all()

def get_user_likes(db: Session, user_guid: str):
    return db.query(models.Swipe.product_guid).filter(
        models.Swipe.user_guid == user_guid,
        models.Swipe.direction == SwipeDirection.like
    ).all()