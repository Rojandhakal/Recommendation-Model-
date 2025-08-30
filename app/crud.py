from sqlalchemy.orm import Session
from app import models, schemas
from app.models import SwipeDirection

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(username=user.username)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_all_users(db: Session):
    return db.query(models.User).all()

def create_product(db: Session, product: schemas.ProductBase, owner_id: int):
    db_product = models.Product(
        name=product.name,
        category=product.category,
        subcategory=product.subcategory,
        color=product.color,
        gender=product.gender,
        description=product.description,
        condition=product.condition,
        owner_id=owner_id
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def get_all_products(db: Session):
    return db.query(models.Product).all()

def get_product_details(db: Session, product_ids: list[int]):
    if not product_ids:
        return []
    return db.query(models.Product).filter(models.Product.id.in_(product_ids)).all()

def create_swipe(db: Session, swipe: schemas.SwipeBase, user_id: int):
    db_swipe = models.Swipe(
        user_id=user_id,
        product_id=swipe.product_id,
        direction=SwipeDirection(swipe.direction.value if hasattr(swipe.direction, "value") else swipe.direction)
    )
    db.add(db_swipe)
    db.commit()
    db.refresh(db_swipe)
    return db_swipe

def get_user_swipes(db: Session, user_id: int):
    return db.query(models.Swipe).filter(models.Swipe.user_id == user_id).all()

def get_user_likes(db: Session, user_id: int):
    return db.query(models.Swipe.product_id).filter(
        models.Swipe.user_id == user_id,
        models.Swipe.direction == SwipeDirection.like
    ).all()
