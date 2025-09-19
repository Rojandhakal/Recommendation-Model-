from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Wishlist, WishlistItem, User, Product
from app.core.logging import get_logger
import traceback  

router = APIRouter(prefix="/wishlist", tags=["wishlist"])
logger = get_logger("wishlist_api")

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

def get_or_create_wishlist(db: Session, user_id: str):
    wishlist = db.query(Wishlist).filter(Wishlist.user_id == user_id).first()
    if not wishlist:
        wishlist = Wishlist(
            user_id=user_id,       
            created_user=user_id,   
            modified_user=user_id   
        )
        db.add(wishlist)
        db.commit()
        db.refresh(wishlist)
    return wishlist

@router.get("/{user_id}")
def get_wishlist(user_id: str, db: Session = Depends(get_db)):
    try:
        verify_user_exists(db, user_id)
        
        wishlist = db.query(Wishlist).filter(Wishlist.user_id == user_id).first()
        
        if not wishlist:
            return {"items": []}
        
        wishlist_items = db.query(WishlistItem).filter(
            WishlistItem.wishlist_id == wishlist.id  
        ).all()
        
        return {"items": [{"product_id": str(i.product_id)} for i in wishlist_items]}  
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Wishlist fetch failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")  
        raise HTTPException(status_code=500, detail="Failed to fetch wishlist")

@router.post("/{user_id}/items/{product_id}")
def add_to_wishlist(user_id: str, product_id: str, db: Session = Depends(get_db)):
    try:
        verify_user_exists(db, user_id)
        verify_product_exists(db, product_id)
        
        wishlist = get_or_create_wishlist(db, user_id)
        
        existing_item = db.query(WishlistItem).filter(
            WishlistItem.wishlist_id == wishlist.id, 
            WishlistItem.product_id == product_id     
            ).first()
        
        if existing_item:
            raise HTTPException(status_code=400, detail="Product already in wishlist")
        
        wishlist_item = WishlistItem(
            wishlist_id=wishlist.id, 
            product_id=product_id,   
            created_user=user_id,  
            modified_user=user_id  
        )
        db.add(wishlist_item)
        db.commit()
        
        logger.info(f"Added product {product_id} to wishlist for user {user_id}")
        return {"message": "Product added to wishlist"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Add to wishlist failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}") 
        raise HTTPException(status_code=500, detail="Failed to add to wishlist")