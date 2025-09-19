from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User
from app.service.recommender import recommendation_engine
from app.schemas import UserRecommendationsResponse
from app.core.logging import get_logger
from datetime import datetime

router = APIRouter(prefix="/recommendations", tags=["recommendations"])
logger = get_logger("recommendations_api")

def verify_user_exists(db: Session, user_id: str):
    user = db.query(User).filter(User.USER_GUID == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/{user_id}", response_model=UserRecommendationsResponse)
def get_user_recommendations(
    user_id: str,
    num_recommendations: int = Query(10, ge=1, le=50, description="Number of recommendations to return"),
    db: Session = Depends(get_db)
):
    try:
        verify_user_exists(db, user_id)
        
        recommendations = recommendation_engine.get_recommendations(
            user_id=user_id,
            num_recommendations=num_recommendations
        )
        
        algorithm = "lightfm"
        
        if not recommendations:
            logger.info(f"No recommendations found for user {user_id}, returning popular items")
            recommendations = recommendation_engine._get_popular_items(db, num_recommendations)
            algorithm = "popular_fallback"
        
        response = UserRecommendationsResponse(
            user_id=user_id,
            recommendations=recommendations,
            algorithm=algorithm,
            generated_at=datetime.now()
        )
        
        logger.info(f"Generated {len(recommendations)} recommendations for user {user_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Recommendation generation failed for user {user_id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to generate recommendations"
        )

@router.post("/train-model")
def train_recommendation_model():
    try:
        logger.info("Manual model training triggered")
        recommendation_engine.train_model()
        
        from app.core.config import get_settings
        settings = get_settings()
        recommendation_engine.save_model(settings.MODEL_PATH)
        
        return {
            "message": "Model trained and saved successfully",
            "model_trained": recommendation_engine.is_trained
        }
        
    except Exception as e:
        logger.error(f"Model training failed: {e}")
        raise HTTPException(status_code=500, detail="Model training failed")