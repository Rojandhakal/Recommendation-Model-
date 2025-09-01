from app.database import SessionLocal
from app.service import recommender

def main():
    db = SessionLocal()
    print("Starting training process...")

    # Force retraining and saving
    recommender.initialize_model(db, force_retrain=True)

    print("Training pipeline completed successfully!")

if __name__ == "__main__":
    main()
