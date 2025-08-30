from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class SwipeDirection(enum.Enum):
    like = "like"
    dislike = "dislike"
    cart = "cart"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True, unique=True)

    swipes = relationship("Swipe", back_populates="user")
    products = relationship("Product", back_populates="owner")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category = Column(String)
    subcategory = Column(String)
    color = Column(String)
    gender = Column(String)
    brand = Column(String, nullable=True)     
    size = Column(String, nullable=True)       
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="products")

    description = Column(String, nullable=True)
    condition = Column(String, nullable=True)
    price = Column(Integer, nullable=True) 



class Swipe(Base):
    __tablename__ = "swipes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    direction = Column(Enum(SwipeDirection))

    user = relationship("User", back_populates="swipes")
    product = relationship("Product")
