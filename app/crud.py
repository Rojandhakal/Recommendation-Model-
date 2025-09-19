from typing import List
from sqlalchemy.orm import Session
from app import schemas
from app.db import models
from app.db.models import SwipeDirection
from app.core.logging import get_logger

logger = get_logger("SwipeCRUD")


def create_swipe(db: Session, swipe: schemas.SwipeBase, user_guid: str) -> models.Swipe:
    """
    Create a new swipe record in the database.
    """
    try:
        direction_value = swipe.direction.value if hasattr(swipe.direction, "value") else swipe.direction
        db_swipe = models.Swipe(
            user_guid=user_guid,
            product_guid=swipe.product_guid,
            direction=SwipeDirection(direction_value)
        )
        db.add(db_swipe)
        db.commit()
        db.refresh(db_swipe)

        logger.info(f"User {user_guid} swiped '{db_swipe.direction}' on product {swipe.product_guid}")
        return db_swipe

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create swipe for user {user_guid}: {e}")
        raise


def get_user_swipes(db: Session, user_guid: str) -> List[models.Swipe]:
    """
    Get all swipes made by a specific user.
    """
    try:
        swipes = db.query(models.Swipe).filter(models.Swipe.user_guid == user_guid).all()
        logger.info(f"Fetched {len(swipes)} swipes for user {user_guid}")
        return swipes
    except Exception as e:
        logger.error(f"Failed to fetch swipes for user {user_guid}: {e}")
        raise


def get_user_likes(db: Session, user_guid: str) -> List[str]:
    """
    Get all product GUIDs that the user has liked.
    """
    try:
        liked_products = [
            p[0] for p in db.query(models.Swipe.product_guid)
                         .filter(
                             models.Swipe.user_guid == user_guid,
                             models.Swipe.direction == SwipeDirection.like
                         )
                         .all()
        ]
        logger.info(f"User {user_guid} liked {len(liked_products)} products")
        return liked_products
    except Exception as e:
        logger.error(f"Failed to fetch liked products for user {user_guid}: {e}")
        raise
