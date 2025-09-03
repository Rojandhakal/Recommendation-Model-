# test_recommend.py
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.service.recommender import initialize_model, get_recommendations

# -----------------------
# Database connection
# -----------------------
# Replace with your actual MySQL credentials from DataGrip
DB_URL = "mysql+pymysql://root:kBRYrXFeTaeYHzwlDaKktTVCxJLhYaCL@monorail.proxy.rlwy.net:38812/thriftko"
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# -----------------------
# Initialize the model
# -----------------------
initialize_model(db)  # loads or trains the LightFM model

# -----------------------
# Test recommendations
# -----------------------
def test_recommendations(user_guid: str, db):
    recs = get_recommendations(user_guid, db=db)
    if recs:
        print(f"Top {len(recs)} recommendations for User {user_guid}:")
        for r in recs:
            print(r)
    else:
        print(f"No recommendations found for User {user_guid}.")

# -----------------------
# Example usage
# -----------------------
if __name__ == "__main__":
    user_guid = "00357f46-38f2-4a88-b5db-a4f066201423"  # Replace with a real user GUID
    test_recommendations(user_guid, db)
