from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey, Enum, Boolean, UniqueConstraint
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

    # UC004A: Edit Profile fields
    address = Column(Text, nullable=True)
    emergency_contact = Column(String(15), nullable=True)
    preferences = Column(Text, nullable=True)
    profile_photo = Column(String(500), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER)
    
    # UC003: Email verification and account status
    email_verified = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    
    # UC003: Login attempt tracking for cooldown
    failed_login_attempts = Column(Integer, default=0)
    last_failed_login_at = Column(DateTime, nullable=True)
    
    # UC003: OTP management for email verification
    email_verification_otp = Column(String(6), nullable=True)
    email_verification_otp_expires_at = Column(DateTime, nullable=True)
    
    # UC003: OTP management for password reset
    password_reset_otp = Column(String(6), nullable=True)
    password_reset_otp_expires_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    feeds = relationship("Feed", back_populates="author")
    comments = relationship("FeedComment", back_populates="author")
    membership_requests = relationship("ClubMembershipRequest", back_populates="user")
    tblr_applications = relationship("TBLRMembership", back_populates="user")
    cart_items = relationship("CartItem", back_populates="user")
    vehicles = relationship("Vehicle", back_populates="owner")
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    received_messages = relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver")


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
    likes = relationship("FeedLike", back_populates="feed", cascade="all, delete-orphan")


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


class FeedLike(Base):
    """Likes on feed posts."""
    __tablename__ = "feed_likes"
    __table_args__ = (UniqueConstraint("feed_id", "user_id", name="uq_feed_like_user"),)

    id = Column(Integer, primary_key=True, index=True)
    feed_id = Column(Integer, ForeignKey("feeds.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    feed = relationship("Feed", back_populates="likes")
    user = relationship("User", backref="feed_likes")


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

class Vehicle(Base):
    """UC004: User vehicle details and preferences."""
    __tablename__ = "vehicles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    make = Column(String(100), nullable=False)  # e.g., "Mahindra"
    model = Column(String(100), nullable=False)  # e.g., "Thar"
    year = Column(String(4), nullable=True)
    registration_number = Column(String(50), nullable=True)
    color = Column(String(50), nullable=True)
    mileage = Column(Float, nullable=True)
    is_primary = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="vehicles")


class Message(Base):
    """UC004: In-app chat messages between members."""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")

# ==================== UC004B: EVENT REGISTRATION & PAYMENT ====================

class EventStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class EventDifficulty(str, enum.Enum):
    EASY = "easy"
    MODERATE = "moderate"
    DIFFICULT = "difficult"
    EXTREME = "extreme"


class RegistrationStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    WAITLIST = "waitlist"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"


class Event(Base):
    """UC004B: Club events for off-roading, trails, meetups."""
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    event_date = Column(DateTime, nullable=False)
    location = Column(String(500), nullable=False)
    difficulty_level = Column(Enum(EventDifficulty), default=EventDifficulty.MODERATE)
    required_vehicle_type = Column(String(100), nullable=True)  # e.g., "4x4 SUV"
    max_participants = Column(Integer, nullable=False)  # Registration limit
    current_participants = Column(Integer, default=0)
    registration_deadline = Column(DateTime, nullable=False)
    event_fee = Column(Float, nullable=False)  # Base fee (includes driver)
    per_person_charge = Column(Float, default=0.0)  # Extra charge per co-passenger
    safety_requirements = Column(Text, nullable=True)
    status = Column(Enum(EventStatus), default=EventStatus.DRAFT)
    image_url = Column(String(500), nullable=True)
    whatsapp_group_template = Column(String(500), nullable=True)  # Template for group link
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = relationship("User", backref="created_events")
    registrations = relationship("EventRegistration", back_populates="event", cascade="all, delete-orphan")


class EventRegistration(Base):
    """UC004B: User registration for events."""
    __tablename__ = "event_registrations"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    registration_status = Column(Enum(RegistrationStatus), default=RegistrationStatus.PENDING)
    num_copassengers = Column(Integer, default=0)
    total_amount = Column(Float, nullable=False)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)
    whatsapp_link = Column(String(500), nullable=True)  # Unique link per participant
    confirmation_sent = Column(Boolean, default=False)
    registered_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    event = relationship("Event", back_populates="registrations")
    user = relationship("User", backref="event_registrations")
    copassengers = relationship("CoPassenger", back_populates="registration", cascade="all, delete-orphan")
    payment = relationship("Payment", backref="event_registration",foreign_keys=[payment_id])


class CoPassenger(Base):
    """UC004B: Co-passenger details for event registrations."""
    __tablename__ = "copassengers"

    id = Column(Integer, primary_key=True, index=True)
    registration_id = Column(Integer, ForeignKey("event_registrations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(20), nullable=False)  # Male, Female, Other
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    registration = relationship("EventRegistration", back_populates="copassengers")


class Payment(Base):
    """UC004B: Payment transactions for event registrations."""
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="INR")
    payment_gateway = Column(String(50), nullable=False)  # "razorpay", "phonepe"
    gateway_payment_id = Column(String(255), nullable=True)  # External payment ID
    gateway_order_id = Column(String(255), nullable=True)  # External order ID
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    payment_method = Column(String(50), nullable=True)  # UPI, Card, Netbanking
    failure_reason = Column(Text, nullable=True)
    payment_metadata = Column(Text, nullable=True)  # JSON for additional data
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="payments")
    event = relationship("Event", backref="payments")
