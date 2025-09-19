from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import Optional, List
from app.db.database import get_db
from app.db.models import Product, ViewCount, User
from app.schemas import ProductResponse
from app.core.logging import get_logger

router = APIRouter(prefix="/products", tags=["products"])
logger = get_logger("products_api")

@router.get("", response_model=List[ProductResponse])
def get_products(
    category: Optional[str] = None,
    brand: Optional[str] = None,
    gender: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    search: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Browse products with optional filtering
    """
    try:
        query = db.query(Product).filter(
            and_(Product.ACTIVE == True, Product.DELETED_TIME.is_(None))
        )

        if category:
            query = query.filter(Product.CATEGORY_SLUG == category)
        
        if brand:
            query = query.filter(Product.BRAND == brand)
            
        if gender:
            query = query.filter(Product.GENDER == gender)

        if min_price is not None:
            query = query.filter(Product.PRICE >= min_price)

        if max_price is not None:
            query = query.filter(Product.PRICE <= max_price)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Product.PRODUCT_NAME.like(search_term), 
                    Product.BRAND.like(search_term),
                    Product.DESCRIPTION.like(search_term)
                )
            )

        total = query.count()
        products = query.offset(offset).limit(limit).all()

        logger.info(f"Retrieved {len(products)} products (total: {total})")
        return products
        
    except Exception as e:
        logger.error(f"Products query error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch products")

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: str, db: Session = Depends(get_db)):
    """
    Get product details by ID
    """
    try:
        product = db.query(Product).filter(
            and_(
                Product.PRODUCT_GUID == product_id,
                Product.ACTIVE == True,
                Product.DELETED_TIME.is_(None)
            )
        ).first()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
            
        return product
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Product fetch error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch product")

@router.post("/{product_id}/view")
def record_product_view(
    product_id: str, 
    user_id: str = Query(..., description="User ID who viewed the product"),
    db: Session = Depends(get_db)
):
    """
    Record a product view for recommendation tracking
    """
    try:
        user_exists = db.query(User.USER_GUID).filter(User.USER_GUID == user_id).first()
        if not user_exists:
            raise HTTPException(status_code=404, detail="User not found")
            
        product = db.query(Product).filter(
            and_(
                Product.PRODUCT_GUID == product_id,
                Product.ACTIVE == True,
                Product.DELETED_TIME.is_(None)
            )
        ).first()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        view_count = db.query(ViewCount).filter(
            and_(ViewCount.user_id == user_id, ViewCount.product_id == product_id)  
        ).first()
        
        if view_count:
            view_count.count += 1 
        else:
            view_count = ViewCount(
                user_id=user_id,  
                product_id=product_id, 
                count=1 
            )
            db.add(view_count)
        
        db.commit()
        
        logger.info(f"User {user_id} viewed product {product_id} (count: {view_count.count})")
        return {"message": "View recorded", "view_count": view_count.count}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"View recording failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to record view")