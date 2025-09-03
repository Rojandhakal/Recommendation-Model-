from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app import crud
from app.service import recommender

router = APIRouter(
    prefix="/recommend",
    tags=["recommend"]
)

@router.on_event("startup")
def load_model_on_startup():
    from app.database import SessionLocal
    db = SessionLocal()
    recommender.initialize_model(db)
    db.close()

def get_product_by_id(db, product_id):
    row = db.execute(text(
        "SELECT id, name, category, subcategory, color, gender, brand, size, description, `condition`, 0 as owner_id "
        "FROM PRODUCTS WHERE id = :pid"
    ), {"pid": product_id}).fetchone()
    if not row:
        return None
    return row

@router.get("/{user_id}")
def get_recommendations(user_id: int, db: Session = Depends(get_db)):
    if not recommender.GLOBAL_MODEL:
        recommender.initialize_model(db)

    recommended_ids = recommender.recommend_products(user_id, num_recs=10, db=db)

    if len(recommended_ids) < 10:
        exclude_ids = set(recommended_ids)
        additional_ids = recommender.recommend_random(db, exclude_ids=list(exclude_ids), top_k=10-len(recommended_ids))
        recommended_ids.extend(additional_ids)

    if not recommended_ids:
        raise HTTPException(status_code=404, detail="No recommendations found for this user.")

    response = []
    for product_id in recommended_ids:
        product = get_product_by_id(db, product_id)
        if product:
            response.append({
                "id": product[0],
                "name": product[1],
                "seller": None,
                "category": product[2],
                "subcategory": product[3],
                "color": product[4],
                "gender": product[5],
                "brand": product[6],
                "size": product[7],
                "description": product[8],
                "condition": product[9],
                "price": None
            })

    return response
