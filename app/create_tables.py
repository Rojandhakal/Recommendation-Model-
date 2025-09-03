from app.database import Base, engine
from app import models

Base.metadata.create_all(bind=engine, tables=[models.Swipe.__table__])
print("SWIPES table created successfully!")
