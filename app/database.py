# Use to set up the connection to the database
from sqlalchemy import create_engine

# Use to define our database models (tables)
from sqlalchemy.ext.declarative import declarative_base

# Used to send data to db or make chnage or read from db
from sqlalchemy.orm import sessionmaker


# "sqlite:///" is for telling we are using sqlite and "./app.db" means db name is that and store in that folder
DATABASE_URL = "sqlite:///./app.db"


# create_engine helps to make a bridge between py code and db, then DB_URL gives where DB is  
# connect_args={"check_same_thread": False} is needed for SQLite to allow multiple threads to use the DB
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)


# autocommit=False is use to make chnage when we commit it 
# autoflush=False means it won’t automatically send changes to the DB until commit
# bind=engine connects the session to our engine (our SQLite database)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Without declarative_base() SQLAlchemy wouldn’t know where to put your tables or how they are connected.
Base = declarative_base()


# get_db() gives your FastAPI endpoint a database session to use, and then automatically closes it when done
def get_db():
    db = SessionLocal()  # create a new session
    try:
        yield db  # provide the session to the caller
    finally:
        db.close()  # make sure the session is closed after use
