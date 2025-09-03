# test.py
import os
import pickle

# Path to your saved LightFM model
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'app', 'service', 'lightfm_model.pkl')

# Load the model
with open(MODEL_PATH, 'rb') as f:
    model = pickle.load(f)

# Dummy product database for demonstration
PRODUCTS = [
    {"guid": "p1", "name": "Skin luga", "category": "pantsmenswear", "size": "L", "color": "#FFC0CB", "price": 800.0},
    {"guid": "p2", "name": "Naya bike", "category": "shoesfootware", "size": "M", "color": "#808000", "price": 800.0},
    {"guid": "p3", "name": "Next level", "category": "pantsmenswear", "size": "XS", "color": "#800080", "price": 2580.0},
    # Add more products here for testing
]

# Example function to get recommendations
def get_recommendations(user_guid: str, top_n=5):
    """
    Returns top N recommended products for a given user_guid
    """
    # For testing, we'll just return the first 'top_n' products
    # Replace this with your LightFM prediction logic
    recommendations = PRODUCTS[:top_n]
    return recommendations

# Test the function
if __name__ == "__main__":
    user_id = "00357f46-38f2-4a88-b5db-a4f066201423"
    recs = get_recommendations(user_id)
    print(f"Top recommendations for User {user_id}:")
    for p in recs:
        print(f" - {p['name']} ({p['category']}) - {p['size']}, {p['color']}, ${p['price']}")
