from lightfm.data import Dataset
from sqlalchemy.orm import Session
from app.db.models import User, Product
from app.core.logging import get_logger

logger = get_logger("ModelUtils")

def build_dataset(users: list[str], items: list[str]) -> Dataset:
    """Builds a LightFM Dataset from given users and items."""
    dataset = Dataset()
    dataset.fit(users=users, items=items)
    logger.info(f"Dataset built with {len(users)} users and {len(items)} items")
    return dataset

def fetch_active_users(db: Session) -> list[str]:
    """Fetch all active users from the database."""
    users = [user.user_guid for user in db.query(User).filter(User.status == "active").all()]
    logger.info(f"Fetched {len(users)} active users")
    return users

def fetch_active_products(db: Session) -> list[str]:
    """Fetch all active and non-deleted products from the database."""
    products = [
        product.product_guid
        for product in db.query(Product)
                         .filter(Product.active == True, Product.deleted_time == None)
                         .all()
    ]
    logger.info(f"Fetched {len(products)} active products")
    return products
