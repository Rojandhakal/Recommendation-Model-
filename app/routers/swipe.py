from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.db.models import Swipe, User, Product, SwipeDirection, CartItem
from app.schemas import SwipeCreate, SwipeResponse
from app.core.logging import get_logger

router = APIRouter(prefix="/swipes", tags=["swipes"])
logger = get_logger("swipes_api")

def verify_user_exists(db: Session, user_id: str):
    user = db.query(User).filter(User.USER_GUID == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def verify_product_exists(db: Session, product_id: str):
    product = db.query(Product).filter(
        Product.PRODUCT_GUID == product_id,
        Product.ACTIVE == True,
        Product.DELETED_TIME.is_(None)
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("/{user_id}", response_model=SwipeResponse)
def create_swipe(
    user_id: str,
    swipe_data: SwipeCreate,
    db: Session = Depends(get_db)
):
    try:
        user = verify_user_exists(db, user_id)
        product = verify_product_exists(db, swipe_data.product_guid)
        
        existing_swipe = db.query(Swipe).filter(
            Swipe.user_guid == user_id,
            Swipe.product_guid == swipe_data.product_guid
        ).first()
        
        if existing_swipe:
            existing_swipe.direction = swipe_data.direction
            db.commit()
            db.refresh(existing_swipe)
            logger.info(f"Updated swipe for user {user_id} on product {swipe_data.product_guid}: {swipe_data.direction}")
            return existing_swipe
        
        new_swipe = Swipe(
            user_guid=user_id,
            product_guid=swipe_data.product_guid,  
            direction=swipe_data.direction
        )
        db.add(new_swipe)
        
        if swipe_data.direction == SwipeDirection.CART:
            existing_cart_item = db.query(CartItem).filter(
                CartItem.user_id == user_id,
                CartItem.product_id == swipe_data.product_guid
            ).first()
            
            if existing_cart_item:
                existing_cart_item.quantity += 1
            else:
                cart_item = CartItem(
                    user_id=user_id,
                    product_id=swipe_data.product_guid, 
                    quantity=1
                )
                db.add(cart_item)
        
        db.commit()
        db.refresh(new_swipe)
        
        logger.info(f"User {user_id} swiped {swipe_data.direction} on product {swipe_data.product_guid}")
        return new_swipe
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Swipe creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create swipe")

@router.get("/{user_id}/liked", response_model=List[str])
def get_user_liked_products(user_id: str, db: Session = Depends(get_db)):
    try:
        verify_user_exists(db, user_id)
        
        liked_products = db.query(Swipe.product_guid).filter(
            Swipe.user_guid == user_id,
            Swipe.direction == SwipeDirection.LIKE
        ).all()
        
        product_ids = [product[0] for product in liked_products]
        
        logger.info(f"User {user_id} has liked {len(product_ids)} products")
        return product_ids
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Liked products retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve liked products")

@router.get("/{user_id}/stats")
def get_user_swipe_stats(user_id: str, db: Session = Depends(get_db)):
    try:
        verify_user_exists(db, user_id)
        
        total_swipes = db.query(Swipe).filter(Swipe.user_guid == user_id).count()
        liked_count = db.query(Swipe).filter(
            Swipe.user_guid == user_id,
            Swipe.direction == SwipeDirection.LIKE
        ).count()
        disliked_count = db.query(Swipe).filter(
            Swipe.user_guid == user_id,
            Swipe.direction == SwipeDirection.DISLIKE
        ).count()
        cart_count = db.query(Swipe).filter(
            Swipe.user_guid == user_id,
            Swipe.direction == SwipeDirection.CART
        ).count()
        
        return {
            "user_id": user_id,
            "total_swipes": total_swipes,
            "liked": liked_count,
            "disliked": disliked_count,
            "added_to_cart": cart_count,
            "like_ratio": round(liked_count / total_swipes * 100, 2) if total_swipes > 0 else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Swipe stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve swipe statistics")