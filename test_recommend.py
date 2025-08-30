from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_recommendations(user_id: int):
    response = client.get(f"/recommend/{user_id}")
    if response.status_code == 200:
        data = response.json()
        print(f"Top {len(data)} recommendations for User {user_id}:")
        for p in data:
            print(
                f"ID: {p['id']}, Name: {p['name']}, Price: {p['price']}, "
                f"Brand: {p['brand']}, Size: {p['size']}, Color: {p['color']}, Category: {p['category']}"
            )
    else:
        print(f"No recommendations found. Status code: {response.status_code}, Detail: {response.json()}")

test_recommendations(user_id=1)
