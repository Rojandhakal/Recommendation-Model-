from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.db.database import get_db
from app.db.models import CartItem, User, Product
from app.schemas import CartItemResponse
from app.core.logging import get_logger

router = APIRouter(prefix="/cart", tags=["cart"])
logger = get_logger("cart_api")

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

@router.get("/{user_id}", response_model=List[CartItemResponse])
def get_user_cart(user_id: str, db: Session = Depends(get_db)):
    try:
        verify_user_exists(db, user_id)
        
        cart_items = db.query(CartItem).options(
            joinedload(CartItem.product)
        ).filter(CartItem.user_id == user_id).all()  
        
        logger.info(f"Retrieved {len(cart_items)} cart items for user {user_id}")
        return cart_items
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cart fetch failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch cart")

@router.post("/{user_id}/items/{product_id}")
def add_item_to_cart(
    user_id: str, 
    product_id: str, 
    quantity: int = Query(1, ge=1, description="Quantity to add"),
    db: Session = Depends(get_db)
):
    try:
        verify_user_exists(db, user_id)
        verify_product_exists(db, product_id)
        
        existing_item = db.query(CartItem).filter(
            CartItem.user_id == user_id,  
            CartItem.product_id == product_id  
        ).first()
        
        if existing_item:
            existing_item.quantity += quantity  
            db.commit()
            db.refresh(existing_item)
            
            logger.info(f"Updated cart item for user {user_id}, product {product_id}, new quantity: {existing_item.quantity}")
            return {"message": "Cart item quantity updated", "quantity": existing_item.quantity}
        else:
            cart_item = CartItem(
                user_id=user_id,  
                product_id=product_id,  
                quantity=quantity  
            )
            db.add(cart_item)
            db.commit()
            
            logger.info(f"Added product {product_id} to cart for user {user_id} with quantity {quantity}")
            return {"message": "Product added to cart", "quantity": quantity}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Add to cart failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to add product to cart")