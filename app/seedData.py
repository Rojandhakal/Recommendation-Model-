from sqlalchemy.orm import Session
from app.database import SessionLocal, Base, engine
from app import models
import random

Base.metadata.create_all(bind=engine)
db: Session = SessionLocal()

usernames = [f"User{i}" for i in range(1, 1001)]
users = []

for name in usernames:
    user = models.User(username=name)
    db.add(user)
    users.append(user)

db.commit()
for user in users:
    db.refresh(user)

colors = ["black", "white", "blue", "red", "green"]
categories = ["shirt", "pants", "jacket", "shoes", "tshirt"]
brands = ["Nike", "Adidas", "Puma", "Zara", "H&M"]
genders = ["men", "women", "unisex"]

clothing_sizes = ["S", "M", "L", "XL", "XXL"]
shoe_sizes = ["38", "40", "42", "44", "46"]

products = []

for i in range(1, 1001):  
    color = random.choice(colors)
    category = random.choice(categories)
    brand = random.choice(brands)
    gender = random.choice(genders)

    if category == "shoes":
        size = random.choice(shoe_sizes)
    else:
        size = random.choice(clothing_sizes)

    name = f"{color.capitalize()} {brand} {category}"

    product = models.Product(
        name=name,
        category=category,
        subcategory=random.choice(["Casual", "Formal", "Sports"]),
        color=color,
        brand=brand,
        gender=gender,
        size=size,
        price=random.randint(10, 200),
        description=f"Description for {name}",
        condition=random.choice(["New", "Used", "Refurbished"])
    )

    db.add(product)
    products.append(product)

db.commit()
for product in products:
    db.refresh(product)

# ---- Swipes ----
for user in users:
    liked_products = random.sample(products, 5)
    for product in liked_products:
        swipe = models.Swipe(
            user_id=user.id,
            product_id=product.id,
            direction="like"
        )
        db.add(swipe)

db.commit()

print("Dummy data added successfully with size & brand!")
