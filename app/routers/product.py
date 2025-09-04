from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas import ProductResponse
from app.database import get_db

router = APIRouter(
    prefix="/products",
    tags=["products"]
)

@router.get("/", response_model=list[ProductResponse])
def list_products(db: Session = Depends(get_db)):
    rows = db.execute(text(
        """
        SELECT PRODUCT_GUID, COLOR, CATEGORY_SLUG, SUB_CATEGORY_ID, DESCRIPTION, BRAND, SIZE
        FROM PRODUCT
        WHERE ACTIVE=1 AND DELETED_TIME IS NULL
        """
    )).fetchall()

    return [
        {
            "product_guid": r[0],
            "color": r[1],
            "category": r[2],
            "subcategory": r[3],
            "description": r[4],
            "brand": r[5],
            "size": r[6],
            "price": r[7] 
        }
        for r in rows
    ]
