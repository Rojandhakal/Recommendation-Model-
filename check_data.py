from sqlalchemy import create_engine, text

# Replace with your actual DB connection string
DB_URL = "mysql+pymysql://root:kBRYrXFeTaeYHzwlDaKktTVCxJLhYaCL@monorail.proxy.rlwy.net:38812/thriftko"

engine = create_engine(DB_URL)

with engine.connect() as conn:
    print("Connected to database!")

    # List all tables
    tables = conn.execute(text("SHOW TABLES")).fetchall()
    print("Tables:", tables)

    # Sample data from USERS table
    users = conn.execute(text("SELECT * FROM USERS LIMIT 5")).fetchall()
    print("Users (sample):")
    for u in users:
        print(u)

    # Sample data from PRODUCT table
    products = conn.execute(text("SELECT * FROM PRODUCT LIMIT 5")).fetchall()
    print("Products (sample):")
    for p in products:
        print(p)

    # Sample data from SWIPES table
    swipes = conn.execute(text("SELECT * FROM SWIPES LIMIT 5")).fetchall()
    print("Swipes (sample):")
    for s in swipes:
        print(s)
