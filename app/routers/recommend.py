from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
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


@router.get("/{user_id}")
def get_recommendations(user_id: int, db: Session = Depends(get_db)):
    """
    Get top recommended products for a user by ID.
    Always returns exactly 10 products, mixing content-based, collaborative, and random items.
    """
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
        product = crud.get_product(db, product_id)
        if product:
            response.append({
                "id": product.id,
                "name": product.name,
                "seller": product.owner.username if product.owner else None,
                "category": product.category,
                "subcategory": product.subcategory,
                "color": product.color,
                "gender": product.gender,
                "brand": getattr(product, "brand", None),
                "size": getattr(product, "size", None),
                "description": product.description,
                "condition": product.condition,
                "price": product.price
            })

    return response
