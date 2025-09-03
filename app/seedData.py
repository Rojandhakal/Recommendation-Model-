from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import SessionLocal, Base, engine
from app import models
import random
from datetime import datetime

Base.metadata.create_all(bind=engine)

db: Session = SessionLocal()

db.query(models.Swipe).delete()
db.commit()

db.execute(text("ALTER TABLE SWIPES AUTO_INCREMENT = 1"))
db.commit()

all_user_guids = [r[0] for r in db.execute(text("SELECT USER_GUID FROM USERS WHERE STATUS='active'")).fetchall()]
all_product_guids = [r[0] for r in db.execute(text("SELECT PRODUCT_GUID FROM PRODUCT WHERE ACTIVE=1 AND DELETED_TIME IS NULL")).fetchall()]

directions = ["like", "dislike", "cart"]
swipes = []

for user_guid in all_user_guids:
    selected_products = random.sample(all_product_guids, min(5, len(all_product_guids)))
    for product_guid in selected_products:
        direction = random.choices(directions, weights=[0.6, 0.3, 0.1])[0]
        swipes.append(
            models.Swipe(
                user_guid=user_guid,
                product_guid=product_guid,
                direction=direction,
                created_time=datetime.now()
            )
        )

db.bulk_save_objects(swipes)
db.commit()

print(f"SWIPES table seeded successfully with {len(swipes)} entries!")
