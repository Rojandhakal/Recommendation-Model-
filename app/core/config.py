import os
from pathlib import Path
from functools import lru_cache

class Settings:
    BASE_DIR = Path(__file__).resolve().parent
    
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:kBRYrXFeTaeYHzwlDaKktTVCxJLhYaCL@monorail.proxy.rlwy.net:38812/thriftko"
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    MODEL_PATH: str = os.getenv("MODEL_PATH", "app/service/lightfm_model.pkl")    
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "1000"))
    MODEL_EPOCHS: int = int(os.getenv("MODEL_EPOCHS", "30"))
    RECOMMENDATION_CACHE_TTL: int = int(os.getenv("RECOMMENDATION_CACHE_TTL", "3600"))
 
    MODEL_LEARNING_RATE: float = float(os.getenv("MODEL_LEARNING_RATE", "0.05"))
    MODEL_ITEM_ALPHA: float = float(os.getenv("MODEL_ITEM_ALPHA", "1e-6"))
    MODEL_USER_ALPHA: float = float(os.getenv("MODEL_USER_ALPHA", "1e-6"))
    MODEL_MAX_SAMPLED: int = int(os.getenv("MODEL_MAX_SAMPLED", "10"))
    MODEL_RANDOM_STATE: int = int(os.getenv("MODEL_RANDOM_STATE", "42"))
    MODEL_NUM_THREADS: int = int(os.getenv("MODEL_NUM_THREADS", "2"))

@lru_cache()
def get_settings() -> Settings:
    return Settings()