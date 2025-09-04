from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from typing import List
from app.service import recommender
from app.database import get_db
from app.schemas import (
    RecommendationResponse,
    UserResponse,
    ProductResponse,
    SwipeResponse,
)

app = FastAPI(title="Thriftko API")


@app.on_event("startup")
def startup_event():
    db = next(get_db())
    recommender.initialize_model(db, force_retrain=False)


@app.get("/")
def read_root():
    return {"message": "Welcome to Thriftko API!"}


@app.get("/recommend/{user_guid}", response_model=RecommendationResponse)
def get_recommendations(user_guid: str, db: Session = Depends(get_db)):
    rec_ids = recommender.get_recommendations(user_guid, db=db)
    products = {p["id"]: p for p in recommender.fetch_products(db)}
    rec_products = [
        {
            "product_guid": products[pid]["id"],
            "color": products[pid]["color"],
            "category": products[pid]["category"],
            "subcategory": products[pid]["subcategory"],
            "description": products[pid]["description"],
            "brand": products[pid]["brand"],
            "size": products[pid]["size"],
        }
        for pid in rec_ids
        if pid in products
    ]
    return {"user_guid": user_guid, "recommendations": rec_products}


@app.get("/users", response_model=List[UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = recommender.fetch_users(db)
    return [{"user_guid": u} for u in users]


@app.get("/products", response_model=List[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    return [
        {
            "product_guid": p["id"],
            "color": p["color"],
            "category": p["category"],
            "subcategory": p["subcategory"],
            "description": p["description"],
            "brand": p["brand"],
            "size": p["size"],
        }
        for p in recommender.fetch_products(db)
    ]


@app.get("/swipes/{user_guid}", response_model=SwipeResponse)
def get_swipes(user_guid: str, db: Session = Depends(get_db)):
    swipes = db.execute(
        "SELECT product_guid FROM SWIPES WHERE user_guid = :uid AND direction='like'",
        {"uid": user_guid},
    ).fetchall()
    liked_products = [s[0] for s in swipes]
    return {"user_guid": user_guid, "liked_products": liked_products}
