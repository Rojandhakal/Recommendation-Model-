from pydantic import BaseModel
from enum import Enum

class SwipeDirection(str, Enum):
    like = "like"
    dislike = "dislike"
    cart = "cart"

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int

    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    name: str
    category: str
    subcategory: str
    color: str
    gender: str
    description: str
    condition: str

class Product(ProductBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True

class SwipeBase(BaseModel):
    product_id: int
    direction: SwipeDirection

class Swipe(SwipeBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
