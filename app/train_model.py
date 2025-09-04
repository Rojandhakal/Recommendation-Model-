from app.database import SessionLocal
from app.service import recommender

def main():
    db = SessionLocal()
    print("Starting training process...")

    recommender.initialize_model(db, force_retrain=False)

    print("Training pipeline completed successfully!")

if __name__ == "__main__":
    main()
