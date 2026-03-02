from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class User(Base):
    """User model for authentication and profile."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(15), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    feeds = relationship("Feed", back_populates="author")
    comments = relationship("FeedComment", back_populates="author")
    membership_requests = relationship("ClubMembershipRequest", back_populates="user")
    tblr_applications = relationship("TBLRMembership", back_populates="user")
    cart_items = relationship("CartItem", back_populates="user")


class Feed(Base):
    """Community feed posts."""
    __tablename__ = "feeds"
    
    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    image_url = Column(String(500), nullable=True)
    likes_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    author = relationship("User", back_populates="feeds")
    comments = relationship("FeedComment", back_populates="feed", cascade="all, delete-orphan")


class FeedComment(Base):
    """Comments on feed posts."""
    __tablename__ = "feed_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    feed_id = Column(Integer, ForeignKey("feeds.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    feed = relationship("Feed", back_populates="comments")
    author = relationship("User", back_populates="comments")


class Accessory(Base):
    """4x4 Accessories/Products."""
    __tablename__ = "accessories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)  # e.g., "Tires", "Suspension"
    price = Column(Float, nullable=False)
    image_url = Column(String(500), nullable=True)
    stock = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Merchandise(Base):
    """Club merchandise items."""
    __tablename__ = "merchandise"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Float, nullable=False)
    image_url = Column(String(500), nullable=True)
    sizes = Column(String(255), nullable=True)  # JSON: ["S", "M", "L", "XL"]
    colors = Column(String(500), nullable=True)  # JSON: [{"name": "Red", "hex": "#FF0000"}]
    stock = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MembershipStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ClubMembershipRequest(Base):
    """Club membership requests from users."""
    __tablename__ = "club_membership_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(15), nullable=False)
    vehicle_model = Column(String(255), nullable=False)
    vehicle_number = Column(String(50), nullable=False)
    registration_date = Column(DateTime, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(Enum(MembershipStatus), default=MembershipStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="membership_requests")


class TBLRMembership(Base):
    """TBLR Membership applications for new members."""
    __tablename__ = "tblr_memberships"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(15), nullable=False)
    vehicle_model = Column(String(255), nullable=False)
    vehicle_number = Column(String(50), nullable=False)
    experience_level = Column(String(100), nullable=False)  # Beginner, Intermediate, Expert
    motivation = Column(Text, nullable=False)
    status = Column(Enum(MembershipStatus), default=MembershipStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="tblr_applications")


class CartItem(Base):
    """Shopping cart items (accessories or merchandise)."""
    __tablename__ = "cart_items"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_type = Column(String(50), nullable=False)  # "accessory" or "merchandise"
    product_id = Column(Integer, nullable=False)
    quantity = Column(Integer, default=1)
    size = Column(String(50), nullable=True)  # For merchandise
    color = Column(String(50), nullable=True)  # For merchandise
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="cart_items")


class ListingStatus(str, enum.Enum):
    ACTIVE = "active"
    SOLD = "sold"
    DELETED = "deleted"


class Listing(Base):
    """Buy/Sell used car listings."""
    __tablename__ = "listings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Float, nullable=False)
    year = Column(String(4), nullable=False)
    mileage = Column(String(100), nullable=False)
    location = Column(String(255), nullable=False)
    vehicle_model = Column(String(255), nullable=True)
    vehicle_number = Column(String(50), nullable=True)
    image_url = Column(String(500), nullable=True)
    status = Column(Enum(ListingStatus), default=ListingStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    seller = relationship("User", backref="listings")
