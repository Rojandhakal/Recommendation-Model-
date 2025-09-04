from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class SwipeDirection(str, Enum):
    like = "like"
    dislike = "dislike"
    cart = "cart"


class SwipeBase(BaseModel):
    product_id: int
    direction: SwipeDirection


class Swipe(SwipeBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True


# ---------- New Schemas ----------

class UserResponse(BaseModel):
    user_guid: str


class ProductResponse(BaseModel):
    product_guid: str
    color: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    description: Optional[str] = None
    brand: Optional[str] = None
    size: Optional[str] = None


class RecommendationResponse(BaseModel):
    user_guid: str
    recommendations: List[ProductResponse]


class SwipeResponse(BaseModel):
    user_guid: str
    liked_products: List[str]
