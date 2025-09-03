from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas import Product
from app.database import get_db

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)

@router.get("/", response_model=list[Product])
def list_products(db: Session = Depends(get_db)):
    rows = db.execute(text(
        "SELECT id, name, category, subcategory, color, gender, brand, size, description, `condition`, 0 as owner_id "
        "FROM PRODUCTS"
    )).fetchall()

    return [
        {
            "id": r[0],
            "name": r[1],
            "category": r[2],
            "subcategory": r[3],
            "color": r[4],
            "gender": r[5],
            "brand": r[6],
            "size": r[7],
            "description": r[8],
            "condition": r[9],
            "owner_id": r[10]
        }
        for r in rows
    ]
