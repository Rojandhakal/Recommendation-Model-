from app.db.database import engine
from sqlalchemy import text

def create_swipes_table():
    create_table_sql = text("""
    CREATE TABLE IF NOT EXISTS SWIPES (
    ID VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    USER_GUID VARCHAR(36) NOT NULL,
    PRODUCT_GUID VARCHAR(36) NOT NULL,
    DIRECTION ENUM('like', 'dislike', 'cart') NOT NULL,
    CREATED_TIME DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (USER_GUID) REFERENCES USERS(USER_GUID) ON DELETE CASCADE,
    FOREIGN KEY (PRODUCT_GUID) REFERENCES PRODUCT(PRODUCT_GUID) ON DELETE CASCADE
    )
    """)

    
    try:
        with engine.connect() as connection:
            with connection.begin():
                connection.execute(create_table_sql)
            print("SWIPES table created successfully!")
    except Exception as e:
        print(f"Error creating table: {e}")

if __name__ == "__main__":
    create_swipes_table()