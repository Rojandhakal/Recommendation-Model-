from pydantic import BaseModel
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
