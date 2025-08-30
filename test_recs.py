from app.database import SessionLocal
from app import crud
from app.service.recommender import initialize_model, recommend_products

db = SessionLocal()

initialize_model(db, force_retrain=False)

users = crud.get_all_users(db)
products = crud.get_all_products(db)
print(" Users in DB:", [u.id for u in users])
print(" Products in DB:", [p.id for p in products])

for user in users[:10]:
    liked_products = crud.get_user_likes(db, user.id)
    print(f"User {user.id} likes: {liked_products}")

from app.service.recommender import GLOBAL_DATASET
if GLOBAL_DATASET:
    print("Interactions matrix shape:", GLOBAL_DATASET.interactions_shape())

test_user_ids = [1, 500, 1000, 2000] 
for user_id in test_user_ids:
    recs = recommend_products(user_id, num_recs=10)
    print(f"Top recommendations returned for User {user_id}: {recs}\n")

db.close()
