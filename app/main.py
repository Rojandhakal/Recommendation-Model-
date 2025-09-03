from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.service import recommender
from app.database import get_db

app = FastAPI(title="Thriftko API")


@app.on_event("startup")
def startup_event():
    """
    Initialize the LightFM model on app startup.
    """
    db = next(get_db())
    recommender.initialize_model(db, force_retrain=False)


@app.get("/")
def read_root():
    return {"message": "Welcome to Thriftko API!"}


@app.get("/recommend/{user_guid}")
def get_recommendations(user_guid: str, db: Session = Depends(get_db)):
    """
    Get top recommendations for a given user.
    """
    recs = recommender.get_recommendations(user_guid, db=db)
    return {"user_guid": user_guid, "recommendations": recs}
