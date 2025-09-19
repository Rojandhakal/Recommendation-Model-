import random
from app.db.database import SessionLocal
from app.core.logging import get_logger
from sqlalchemy import text

logger = get_logger("SeedSwipesRawSQL")

def seed_swipes_raw_sql():
    """Seed only the SWIPES table with dummy data using raw SQL"""
    db = SessionLocal()
    try:
        logger.info("Starting SWIPES table seeding with raw SQL...")
        
        users = db.execute(text("SELECT USER_GUID FROM USERS")).fetchall()
        products = db.execute(text("SELECT PRODUCT_GUID FROM PRODUCT")).fetchall()
        
        if not users:
            logger.error("No users found in the database!")
            return
        if not products:
            logger.error("No products found in the database!")
            return
            
        logger.info(f"Found {len(users)} users and {len(products)} products")
        
        directions = ['like', 'dislike', 'cart']
        swipe_count = 0
        
        for user in users:
            user_guid = user[0]
            
            num_swipes = random.randint(5, 15)
            user_products = random.sample(products, min(num_swipes, len(products)))
            
            for product in user_products:
                product_guid = product[0]
                direction = random.choice(directions)
                
                insert_sql = text("""
                    INSERT INTO SWIPES (USER_GUID, PRODUCT_GUID, DIRECTION) 
                    VALUES (:user_guid, :product_guid, :direction)
                """)
                
                db.execute(insert_sql, {
                    'user_guid': user_guid,
                    'product_guid': product_guid, 
                    'direction': direction
                })
                swipe_count += 1
        
        db.commit()
        logger.info(f"Seeded {swipe_count} swipes into SWIPES table!")
        
    except Exception as e:
        db.rollback()
        logger.error(f"SWIPES seeding failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_swipes_raw_sql()