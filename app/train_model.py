import os
from app.service.recommender import recommendation_engine
from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger("TrainingPipeline")

def run_training_pipeline() -> None:
    try:
        logger.info("Starting training pipeline...")
        
        recommendation_engine.train_model()
        logger.info("Model trained successfully")
        
        recommendation_engine.save_model(settings.MODEL_PATH)
        logger.info(f"Model saved successfully at {settings.MODEL_PATH}")
        
    except Exception as e:
        logger.exception(f"Training pipeline failed: {e}")
        raise

if __name__ == "__main__":
    run_training_pipeline()