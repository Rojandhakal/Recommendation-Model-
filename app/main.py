from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from app.db.database import engine, Base
from app.service.recommender import recommendation_engine
from app.routers import product, user, recommend, swipe, wishlist, cart
from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Thriftko API application...")

    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    try:
        model_dir = os.path.dirname(settings.MODEL_PATH)
        if model_dir:
            os.makedirs(model_dir, exist_ok=True)
        
        if os.path.exists(settings.MODEL_PATH):
            recommendation_engine.load_model(settings.MODEL_PATH)
            logger.info("Existing model loaded successfully")
        else:
            logger.info("No existing model found. Will train on first recommendation request.")
            
    except Exception as e:
        logger.error(f"Recommendation engine initialization failed: {e}")

    yield

    logger.info("Shutting down Thriftko API application...")

app = FastAPI(
    title="Thriftko API",
    description="Advanced swapping and recommendation system",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(product.router)
app.include_router(user.router)
app.include_router(recommend.router)
app.include_router(swipe.router)
app.include_router(wishlist.router)
app.include_router(cart.router)

@app.get("/")
def root():
    return {
        "message": "Welcome to Thriftko API",
        "version": app.version,
        "docs": "/docs",
        "status": "running"
    }

@app.get("/health")
def health_check():
    try:
        redis_client = recommendation_engine._get_redis()
        redis_status = redis_client is not None and redis_client.ping() if redis_client else False
    except:
        redis_status = False
        
    return {
        "status": "healthy",
        "database": "connected",
        "model_trained": recommendation_engine.is_trained,
        "redis_connected": redis_status,
        "version": app.version
    }