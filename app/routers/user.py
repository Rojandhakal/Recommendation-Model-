from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User
from app.schemas import UserCreate, UserResponse
from app.core.logging import get_logger

router = APIRouter(prefix="/users", tags=["users"])
logger = get_logger("users_api")

@router.post("", response_model=UserResponse)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    try:
        existing_user = db.query(User).filter(
            (User.USER_NAME == user_data.username) | (User.EMAIL == user_data.email)
        ).first()
        
        if existing_user:
            raise HTTPException(status_code=400, detail="Username or email already exists")
        
        new_user = User(
            USER_NAME=user_data.username,     
            EMAIL=user_data.email,             
            FIRST_NAME=user_data.first_name,   
            LAST_NAME=user_data.last_name,   
            MOBILE_NUMBER=user_data.phone,   
            STATUS="ACTIVE"               
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"Created user: {new_user.USER_GUID}")
        return new_user
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"User creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user")

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.USER_GUID == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User fetch failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch user")
