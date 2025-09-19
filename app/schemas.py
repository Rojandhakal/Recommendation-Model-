from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

class SwipeDirection(str, Enum):
    LIKE = "like"
    DISLIKE = "dislike"
    CART = "cart"  


class UserBase(BaseModel):
    username: str = Field(..., alias="USER_NAME")
    email: str = Field(..., alias="EMAIL")
    first_name: Optional[str] = Field(None, alias="FIRST_NAME")
    last_name: Optional[str] = Field(None, alias="LAST_NAME")
    phone: Optional[str] = Field(None, alias="MOBILE_NUMBER")

class UserCreate(UserBase):
    pass

class UserResponse(BaseModel):
    username: str = Field(alias="USER_NAME")
    email: str = Field(alias="EMAIL")
    first_name: Optional[str] = Field(None, alias="FIRST_NAME")
    last_name: Optional[str] = Field(None, alias="LAST_NAME")
    phone: Optional[str] = Field(None, alias="MOBILE_NUMBER")
    id: str = Field(alias="USER_GUID")
    status: Optional[str] = Field(None, alias="STATUS")
    profile_picture: Optional[str] = Field(None, alias="PROFILE_PICTURE")
    date_of_birth: Optional[datetime] = Field(None, alias="DATE_OF_BIRTH")
    latitude: Optional[float] = Field(None, alias="LATITUDE")
    longitude: Optional[float] = Field(None, alias="LONGITUDE")
    created_time: Optional[datetime] = Field(None, alias="CREATED_TIME")
    modified_time: Optional[datetime] = Field(None, alias="MODIFIED_TIME")
    created_user: Optional[str] = Field(None, alias="CREATED_USER")
    modified_user: Optional[str] = Field(None, alias="MODIFIED_USER")
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class ProductBase(BaseModel):
    name: str = Field(..., alias="PRODUCT_NAME")
    description: Optional[str] = Field(None, alias="DESCRIPTION")
    category_slug: Optional[str] = Field(None, alias="CATEGORY_SLUG")
    brand: Optional[str] = Field(None, alias="BRAND")
    gender: Optional[str] = Field(None, alias="GENDER")
    price: float = Field(..., alias="PRICE")
    active: Optional[bool] = Field(None, alias="ACTIVE")
    image_path: Optional[str] = Field(None, alias="IMAGE_PATH")
    color: Optional[str] = Field(None, alias="COLOR")
    size: Optional[str] = Field(None, alias="SIZE")
    product_slug: Optional[str] = Field(None, alias="PRODUCT_SLUG")
    collection_slug: Optional[str] = Field(None, alias="COLLECTION_SLUG")
    sub_category_id: Optional[str] = Field(None, alias="SUB_CATEGORY_ID")
    wishlist_count: Optional[int] = Field(None, alias="WISHLIST_COUNT")
    user_guid: Optional[str] = Field(None, alias="USER_GUID")

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: str = Field(alias="PRODUCT_GUID")
    deleted_time: Optional[datetime] = Field(None, alias="DELETED_TIME")
    created_time: Optional[datetime] = Field(None, alias="CREATED_TIME")
    modified_time: Optional[datetime] = Field(None, alias="MODIFIED_TIME")
    created_user: Optional[str] = Field(None, alias="CREATED_USER")
    modified_user: Optional[str] = Field(None, alias="MODIFIED_USER")
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class ProductRecommendation(BaseModel):
    id: str = Field(alias="PRODUCT_GUID")
    name: str = Field(alias="PRODUCT_NAME")
    description: Optional[str] = Field(None, alias="DESCRIPTION")
    price: float = Field(..., alias="PRICE")
    image_path: Optional[str] = Field(None, alias="IMAGE_PATH")
    brand: Optional[str] = Field(None, alias="BRAND")
    category_slug: Optional[str] = Field(None, alias="CATEGORY_SLUG")
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class UserRecommendationsResponse(BaseModel):
    user_id: str
    recommendations: List[ProductRecommendation]
    algorithm: Optional[str] = "default" 
    generated_at: datetime = Field(default_factory=datetime.now)
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class WishlistBase(BaseModel):
    user_id: str = Field(..., alias="USER_GUID")

class WishlistCreate(WishlistBase):
    pass

class WishlistResponse(WishlistBase):
    id: str = Field(alias="WISHLIST_GUID")
    created_time: Optional[datetime] = Field(None, alias="CREATED_TIME")
    created_user: Optional[str] = Field(None, alias="CREATED_USER")
    modified_time: Optional[datetime] = Field(None, alias="MODIFIED_TIME")
    modified_user: Optional[str] = Field(None, alias="MODIFIED_USER")
    deleted_time: Optional[datetime] = Field(None, alias="DELETED_TIME")
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class WishlistItemBase(BaseModel):
    wishlist_id: str = Field(..., alias="WISHLIST_ID")
    product_id: str = Field(..., alias="PRODUCT_ID")

class WishlistItemCreate(WishlistItemBase):
    pass

class WishlistItemResponse(WishlistItemBase):
    id: str = Field(alias="WISHLIST_ITEM_GUID")
    created_time: Optional[datetime] = Field(None, alias="CREATED_TIME")
    created_user: Optional[str] = Field(None, alias="CREATED_USER")
    modified_time: Optional[datetime] = Field(None, alias="MODIFIED_TIME")
    modified_user: Optional[str] = Field(None, alias="MODIFIED_USER")
    deleted_time: Optional[datetime] = Field(None, alias="DELETED_TIME")
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class CartItemBase(BaseModel):
    user_id: str = Field(..., alias="user_id")
    product_id: str = Field(..., alias="product_id")
    quantity: int = Field(1, alias="quantity")

class CartItemCreate(CartItemBase):
    pass

class CartItemResponse(CartItemBase):
    id: str = Field(alias="id")
    created_time: Optional[datetime] = Field(None, alias="created_time")
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class ViewCountBase(BaseModel):
    user_id: str = Field(..., alias="USER_ID")
    product_id: str = Field(..., alias="PRODUCT_ID")
    count: int = Field(1, alias="COUNT")

class ViewCountCreate(ViewCountBase):
    pass

class ViewCountResponse(ViewCountBase):
    id: str = Field(alias="VIEW_COUNT_ID")
    created_time: Optional[datetime] = Field(None, alias="CREATED_TIME")
    created_user: Optional[str] = Field(None, alias="CREATED_USER")
    modified_time: Optional[datetime] = Field(None, alias="MODIFIED_TIME")
    modified_user: Optional[str] = Field(None, alias="MODIFIED_USER")
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )
class SwipeBase(BaseModel):
    user_guid: str = Field(..., alias="user_guid")
    product_guid: str = Field(..., alias="product_guid")
    direction: SwipeDirection = Field(..., alias="direction")

class SwipeCreate(SwipeBase):
    pass

class SwipeResponse(SwipeBase):
    id: str = Field(alias="id")
    created_time: Optional[datetime] = Field(None, alias="created_time")
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )