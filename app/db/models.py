import uuid
import enum
from sqlalchemy import Column, String, Float, ForeignKey, Integer, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class SwipeDirection(enum.Enum):
    LIKE = "like"
    DISLIKE = "dislike"
    CART = "cart"


class User(Base):
    __tablename__ = "USERS"

    USER_GUID = Column(String(36), primary_key=True, default=generate_uuid)
    USER_NAME = Column(String(255))  
    EMAIL = Column(String(255))
    FIRST_NAME = Column(String(255))
    LAST_NAME = Column(String(255))
    MOBILE_NUMBER = Column(String(255))  
    STATUS = Column(String(20))
    PROFILE_PICTURE = Column(String(255))
    DATE_OF_BIRTH = Column(DateTime)
    LATITUDE = Column(Float) 
    LONGITUDE = Column(Float)  
    CREATED_TIME = Column(DateTime)
    MODIFIED_TIME = Column(DateTime)
    CREATED_USER = Column(String(255))
    MODIFIED_USER = Column(String(255))

    wishlists = relationship("Wishlist", back_populates="user", cascade="all, delete-orphan")
    cart_items = relationship("CartItem", back_populates="user", cascade="all, delete-orphan")
    swipes = relationship("Swipe", back_populates="user", cascade="all, delete-orphan")
    view_counts = relationship("ViewCount", back_populates="user", cascade="all, delete-orphan")



class Product(Base):
    __tablename__ = "PRODUCT"

    PRODUCT_GUID = Column(String(36), primary_key=True, default=generate_uuid)
    PRODUCT_NAME = Column(String(255), nullable=False) 
    DESCRIPTION = Column(String(255)) 
    CATEGORY_SLUG = Column(String(255))
    BRAND = Column(String(255))
    GENDER = Column(String(20))
    PRICE = Column(Float, nullable=False)
    ACTIVE = Column(Boolean)
    DELETED_TIME = Column(DateTime)
    CREATED_TIME = Column(DateTime)
    MODIFIED_TIME = Column(DateTime)
    IMAGE_PATH = Column(String(255))
    COLOR = Column(String(255))
    SIZE = Column(String(255))
    PRODUCT_SLUG = Column(String(255))
    COLLECTION_SLUG = Column(String(255))
    SUB_CATEGORY_ID = Column(String(255))
    WISHLIST_COUNT = Column(Integer)
    CREATED_USER = Column(String(255))
    MODIFIED_USER = Column(String(255))
    USER_GUID = Column(String(36))

    wishlist_items = relationship("WishlistItem", back_populates="product", cascade="all, delete-orphan")
    cart_items = relationship("CartItem", back_populates="product", cascade="all, delete-orphan")
    swipes = relationship("Swipe", back_populates="product", cascade="all, delete-orphan")
    view_counts = relationship("ViewCount", back_populates="product", cascade="all, delete-orphan")

class Wishlist(Base):
    __tablename__ = "WISHLIST"
    __table_args__ = {'extend_existing': True}  

    id = Column("WISHLIST_GUID", String(36), primary_key=True, default=generate_uuid)
    user_id = Column("USER_GUID", String(36), ForeignKey("USERS.USER_GUID", ondelete="CASCADE"), nullable=False)
    created_time = Column("CREATED_TIME", DateTime, default=func.now())
    created_user = Column("CREATED_USER", String(255))
    modified_time = Column("MODIFIED_TIME", DateTime, default=func.now(), onupdate=func.now())
    modified_user = Column("MODIFIED_USER", String(255))
    deleted_time = Column("DELETED_TIME", DateTime)

    user = relationship("User", back_populates="wishlists")
    items = relationship("WishlistItem", back_populates="wishlist", cascade="all, delete-orphan")

class WishlistItem(Base):
    __tablename__ = "WISHLIST_ITEM"

    id = Column("WISHLIST_ITEM_GUID", String(36), primary_key=True, default=generate_uuid)
    wishlist_id = Column("WISHLIST_ID", String(36), ForeignKey("WISHLIST.WISHLIST_GUID", ondelete="CASCADE"), nullable=False)
    product_id = Column("PRODUCT_ID", String(36), ForeignKey("PRODUCT.PRODUCT_GUID", ondelete="CASCADE"), nullable=False)
    created_time = Column("CREATED_TIME", DateTime, default=func.now())
    created_user = Column("CREATED_USER", String(255))
    modified_time = Column("MODIFIED_TIME", DateTime, default=func.now(), onupdate=func.now())
    modified_user = Column("MODIFIED_USER", String(255))
    deleted_time = Column("DELETED_TIME", DateTime)

    wishlist = relationship("Wishlist", back_populates="items")
    product = relationship("Product", back_populates="wishlist_items")

class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("USERS.USER_GUID", ondelete="CASCADE"), nullable=False)
    product_id = Column(String(36), ForeignKey("PRODUCT.PRODUCT_GUID", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, default=1)
    created_time = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")

class ViewCount(Base):
    __tablename__ = "VIEW_COUNT"

    id = Column("VIEW_COUNT_ID", String(36), primary_key=True, default=generate_uuid)
    user_id = Column("USER_ID", String(36), ForeignKey("USERS.USER_GUID", ondelete="CASCADE"), nullable=False)
    product_id = Column("PRODUCT_ID", String(36), ForeignKey("PRODUCT.PRODUCT_GUID", ondelete="CASCADE"), nullable=False)
    count = Column("COUNT", Integer, default=1)
    created_time = Column("CREATED_TIME", DateTime, default=func.now())
    created_user = Column("CREATED_USER", String(255))
    modified_time = Column("MODIFIED_TIME", DateTime, default=func.now(), onupdate=func.now())
    modified_user = Column("MODIFIED_USER", String(255))

    user = relationship("User", back_populates="view_counts")
    product = relationship("Product", back_populates="view_counts")

class Swipe(Base):
    __tablename__ = "SWIPES"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_guid = Column(String(36), ForeignKey("USERS.USER_GUID", ondelete="CASCADE"), nullable=False)
    product_guid = Column(String(36), ForeignKey("PRODUCT.PRODUCT_GUID", ondelete="CASCADE"), nullable=False)
    
    direction = Column(Enum(SwipeDirection, values_callable=lambda x: [e.value for e in x]), nullable=False)
    
    created_time = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="swipes")
    product = relationship("Product", back_populates="swipes")