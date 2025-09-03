from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class SwipeDirection(enum.Enum):
    like = "like"
    dislike = "dislike"
    cart = "cart"

class User(Base):
    __tablename__ = "USERS"

    USER_GUID = Column(String(255), primary_key=True, index=True)
    USER_NAME = Column(String(255))
    EMAIL = Column(String(255))
    FIRST_NAME = Column(String(255))
    LAST_NAME = Column(String(255))
    MOBILE_NUMBER = Column(String(20))
    STATUS = Column(String(50))
    PROFILE_PICTURE = Column(String(255))
    DATE_OF_BIRTH = Column(DateTime)
    LATITUDE = Column(String(50))
    LONGITUDE = Column(String(50))
    CREATED_TIME = Column(DateTime, default=datetime.utcnow)
    MODIFIED_TIME = Column(DateTime)
    CREATED_USER = Column(String(255))
    MODIFIED_USER = Column(String(255))

    swipes = relationship("Swipe", back_populates="user")

class Product(Base):
    __tablename__ = "PRODUCT"

    PRODUCT_GUID = Column(String(255), primary_key=True, index=True)
    PRODUCT_NAME = Column(String(255))
    PRODUCT_SLUG = Column(String(255))
    DESCRIPTION = Column(String(500))
    PRICE = Column(Integer)
    IMAGE_PATH = Column(String(255))
    BRAND = Column(String(255))
    CATEGORY_SLUG = Column(String(255))
    COLLECTION_SLUG = Column(String(255))
    COLOR = Column(String(50))
    SIZE = Column(String(50))
    GENDER = Column(String(50))
    SUB_CATEGORY_ID = Column(Integer)
    WISHLIST_COUNT = Column(Integer)
    ACTIVE = Column(String(10))
    DELETED_TIME = Column(DateTime)
    CREATED_TIME = Column(DateTime, default=datetime.utcnow)
    MODIFIED_TIME = Column(DateTime)
    CREATED_USER = Column(String(255))
    MODIFIED_USER = Column(String(255))
    USER_GUID = Column(String(255), ForeignKey("USERS.USER_GUID"))

    swipes = relationship("Swipe", back_populates="product")

class Swipe(Base):
    __tablename__ = "SWIPES"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_guid = Column(String(255), ForeignKey("USERS.USER_GUID"))
    product_guid = Column(String(255), ForeignKey("PRODUCT.PRODUCT_GUID"))
    direction = Column(Enum(SwipeDirection))
    created_time = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="swipes")
    product = relationship("Product", back_populates="swipes")
