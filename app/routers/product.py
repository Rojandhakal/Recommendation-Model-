from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import schemas, crud
from app.database import get_db


router = APIRouter(
    prefix="/products",
    tags=["Products"]
)

@router.post("/", response_model=schemas.Product)
def create_product(product: schemas.ProductBase, owner_id: int, db: Session = Depends(get_db)):
    return crud.create_product(db, product, owner_id)

@router.get("/", response_model=list[schemas.Product])
def list_products(db: Session = Depends(get_db)):
    return crud.get_all_products(db)

