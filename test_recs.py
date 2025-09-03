from sqlalchemy import text
from app.database import SessionLocal
from app.service.recommender import initialize_model, recommend_products

# Open a database session
db = SessionLocal()

# Initialize or load the LightFM model
initialize_model(db, force_retrain=False)

# List of user IDs to test recommendations
test_user_ids = [1, 500, 1000, 2000]

for user_id in test_user_ids:
    # Get recommended product GUIDs
    recs = recommend_products(user_id, num_recs=10, db=db)
    
    # Fetch product details from the database
    product_details = []
    for pid in recs:
        row = db.execute(
            text(
                "SELECT PRODUCT_NAME, CATEGORY_SLUG, PRICE, BRAND, SIZE, COLOR "
                "FROM PRODUCT WHERE PRODUCT_GUID = :pid"
            ),
            {"pid": pid}
        ).fetchone()
        if row:
            product_details.append({
                "name": row[0],
                "category": row[1],
                "price": row[2],
                "brand": row[3],
                "size": row[4],
                "color": row[5]
            })
    
    # Format recommendations for display
    readable_recs = [
        f"{p['name']} ({p['category']}) - {p['brand']}, {p['size']}, {p['color']}, ${p['price']}" 
        for p in product_details
    ]
    
    print(f"Top recommendations for User {user_id}:")
    for rec in readable_recs:
        print(f" - {rec}")
    print("\n")

# Close the database session
db.close()
