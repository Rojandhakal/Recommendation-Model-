from app.database import SessionLocal
from app import crud
from app.service.recommender import initialize_model, recommend_products

# Create a database session
db = SessionLocal()

initialize_model(db, force_retrain=False)

# ... [the rest of your printing code remains the same] ...

test_user_ids = [1, 500, 1000, 2000] 
for user_id in test_user_ids:
    # PASS THE DATABASE SESSION 'db' TO THE FUNCTION
    recs = recommend_products(user_id, num_recs=10, db=db)
    print(f"Top recommendations returned for User {user_id}: {recs}\n")

# Close the session when done
db.close()