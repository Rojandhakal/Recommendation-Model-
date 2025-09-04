from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
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

def get_product_details(db: Session, product_guid: str):
    row = db.execute(text(
        """
        SELECT product_guid, product_name, user_guid, category_slug, sub_category_id, color,
               description, active
        FROM product
        WHERE product_guid = :pid AND deleted_time IS NULL
        """
    ), {"pid": product_guid}).fetchone()

    if not row:
        return None

    return {
        "product_guid": row[0],
        "name": row[1],
        "seller": row[2],
        "category": row[3],
        "subcategory": row[4],
        "color": row[5],
        "description": row[6],
        "condition": row[7]
    }

@router.get("/{user_guid}")
def get_recommendations(user_guid: str, db: Session = Depends(get_db)):
    if not recommender.GLOBAL_MODEL:
        recommender.initialize_model(db)

    recommended_ids = recommender.recommend_products(user_guid, num_recs=10, db=db)

    if len(recommended_ids) < 10:
        exclude_ids = set(recommended_ids)
        additional_ids = recommender.recommend_random(db, exclude_ids=list(exclude_ids), top_k=10-len(recommended_ids))
        recommended_ids.extend(additional_ids)

    if not recommended_ids:
        raise HTTPException(status_code=404, detail="No recommendations found for this user.")

    response = [get_product_details(db, pid) for pid in recommended_ids if get_product_details(db, pid)]

    return {
        "user_guid": user_guid,
        "recommendations": response
    }
