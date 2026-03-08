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
    membership_requests = relationship(
        "ClubMembershipRequest",
        back_populates="user",
        foreign_keys="ClubMembershipRequest.user_id"
    )
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


class Vendor(Base):
    """UC004D: Vendors who sell 4x4 accessories."""
    __tablename__ = "vendors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    whatsapp_number = Column(String(15), nullable=False)  # International format
    payment_gateway = Column(String(50), nullable=False)  # e.g., "razorpay", "custom"
    payment_gateway_key = Column(String(500), nullable=True)  # API key for payment gateway
    payment_gateway_url = Column(String(500), nullable=True)  # Redirect URL for payment
    status = Column(String(20), default="active")  # "active", "inactive"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    accessories = relationship("Accessory", back_populates="vendor", cascade="all, delete-orphan")
    orders = relationship("AccessoryOrder", back_populates="vendor")


class Accessory(Base):
    """4x4 Accessories/Products."""
    __tablename__ = "accessories"
    
    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    long_description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False)  # e.g., "Recovery Gear", "Lighting", "Suspension"
    price = Column(Float, nullable=False)
    image_url = Column(String(500), nullable=True)
    images = Column(String(2000), nullable=True)  # JSON list of image URLs
    stock = Column(Integer, default=0)
    features = Column(String(2000), nullable=True)  # JSON list of features
    compatibility = Column(String(500), nullable=True)  # Compatible vehicle types
    brand = Column(String(100), nullable=True)
    rating = Column(Float, default=0.0)
    reviews_count = Column(Integer, default=0)
    is_featured = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    vendor = relationship("Vendor", back_populates="accessories")
    order_items = relationship("AccessoryOrderItem", back_populates="accessory")


class Merchandise(Base):
    """UC004E: Club merchandise items (apparel, stickers, accessories)."""
    __tablename__ = "merchandise"
    
    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)  # Vendor who sells this merchandise
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    long_description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False)  # e.g., "Apparel", "Stickers", "Accessories"
    price = Column(Float, nullable=False)
    image_url = Column(String(500), nullable=True)  # Primary image (backward compatible)
    images = Column(String(2000), nullable=True)  # JSON list of image URLs
    sizes = Column(String(500), nullable=True)  # JSON: [{"id": "m", "size": "M", "label": "Medium"}]
    colors = Column(String(500), nullable=True)  # JSON: [{"id": "red", "name": "Red", "hex": "#FF0000"}]
    stock = Column(Integer, default=0)
    features = Column(String(2000), nullable=True)  # JSON list of features
    material = Column(String(100), nullable=True)  # e.g., "100% Cotton", "Polyester"
    brand = Column(String(100), nullable=True)
    rating = Column(Float, default=0.0)
    reviews = Column(Integer, default=0)  # Number of reviews
    is_featured = Column(Boolean, default=False)
    is_on_sale = Column(Boolean, default=False)
    discounted_price = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    vendor = relationship("Vendor", backref="merchandise")
    order_items = relationship("MerchandiseOrderItem", back_populates="merchandise")


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

    # UC005: Auto-filled and editable membership profile fields
    residential_address = Column(Text, nullable=True)
    emergency_contact = Column(String(15), nullable=True)
    vehicle_fuel_type = Column(String(20), nullable=True)  # petrol/diesel
    vehicle_transmission_type = Column(String(20), nullable=True)  # manual/automatic
    profile_photo_url = Column(String(500), nullable=True)
    rc_document_url = Column(String(500), nullable=True)
    insurance_document_url = Column(String(500), nullable=True)
    aadhaar_document_url = Column(String(500), nullable=True)
    driving_license_document_url = Column(String(500), nullable=True)
    vehicle_modifications = Column(Text, nullable=True)
    additional_info = Column(Text, nullable=True)
    terms_accepted = Column(Boolean, default=False)
    workshop_trail_completed = Column(Boolean, default=False)

    # UC005: Admin review and payment/activation lifecycle
    status = Column(Enum(MembershipStatus), default=MembershipStatus.PENDING)
    payment_status = Column(String(20), default="pending")  # pending/success/failed
    payment_gateway = Column(String(50), nullable=True)
    payment_order_id = Column(String(255), nullable=True)
    payment_id = Column(String(255), nullable=True)
    payment_link_enabled = Column(Boolean, default=False)
    approved_by_admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # UC005: Membership activation artifacts
    membership_id = Column(String(100), unique=True, nullable=True)
    whatsapp_group_name = Column(String(255), nullable=True)
    whatsapp_group_link = Column(String(500), nullable=True)
    whatsapp_join_available = Column(Boolean, default=False)
    activated_at = Column(DateTime, nullable=True)

    # UC005: Basic audit trail (JSON string)
    audit_log = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="membership_requests", foreign_keys=[user_id])
    approved_by_admin = relationship("User", foreign_keys=[approved_by_admin_id])


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


# ==================== UC004D: ACCESSORIES SHOPPING & VENDOR INTEGRATION ====================

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    VENDOR_NOTIFIED = "vendor_notified"
    CANCELLED = "cancelled"


class AccessoryOrder(Base):
    """UC004D: Orders for purchasing accessories through vendors."""
    __tablename__ = "accessory_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for guest checkout
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    order_number = Column(String(50), unique=True, nullable=False)  # e.g., ORD-20260208-001
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255), nullable=False)
    customer_phone = Column(String(15), nullable=False)
    shipping_address = Column(Text, nullable=False)
    total_amount = Column(Float, nullable=False)
    currency = Column(String(3), default="INR")
    payment_gateway = Column(String(50), nullable=False)  # e.g., "razorpay"
    payment_id = Column(String(255), nullable=True)  # External payment ID from vendor gateway
    order_id = Column(String(255), nullable=True)  # External order ID from vendor gateway
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    order_status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    vendor_notification_sent = Column(Boolean, default=False)
    vendor_notification_email_sent = Column(Boolean, default=False)
    vendor_notification_whatsapp_sent = Column(Boolean, default=False)
    user_confirmation_sent = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="accessory_orders")
    vendor = relationship("Vendor", back_populates="orders")
    items = relationship("AccessoryOrderItem", back_populates="order", cascade="all, delete-orphan")


class AccessoryOrderItem(Base):
    """UC004D: Individual items in an accessory order."""
    __tablename__ = "accessory_order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("accessory_orders.id"), nullable=False)
    accessory_id = Column(Integer, ForeignKey("accessories.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)  # Price at time of order
    total_price = Column(Float, nullable=False)  # quantity * unit_price
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    order = relationship("AccessoryOrder", back_populates="items")
    accessory = relationship("Accessory", back_populates="order_items")


# ==================== UC004E: CLUB MERCHANDISE SHOPPING & VENDOR INTEGRATION ====================

class MerchandiseOrder(Base):
    """UC004E: Orders for purchasing club merchandise through vendors."""
    __tablename__ = "merchandise_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for guest checkout
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    order_number = Column(String(50), unique=True, nullable=False)  # e.g., MERCH-20260308-001
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255), nullable=False)
    customer_phone = Column(String(15), nullable=False)
    shipping_address = Column(Text, nullable=False)
    total_amount = Column(Float, nullable=False)
    currency = Column(String(3), default="INR")
    payment_gateway = Column(String(50), nullable=False)  # e.g., "razorpay", "phonepe"
    payment_id = Column(String(255), nullable=True)  # External payment ID from vendor gateway
    order_id = Column(String(255), nullable=True)  # External order ID from vendor gateway
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    order_status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    vendor_notification_sent = Column(Boolean, default=False)
    vendor_notification_email_sent = Column(Boolean, default=False)
    vendor_notification_whatsapp_sent = Column(Boolean, default=False)
    user_confirmation_sent = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="merchandise_orders")
    vendor = relationship("Vendor", backref="merchandise_orders_as_vendor")
    items = relationship("MerchandiseOrderItem", back_populates="order", cascade="all, delete-orphan")


class MerchandiseOrderItem(Base):
    """UC004E: Individual items in a merchandise order."""
    __tablename__ = "merchandise_order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("merchandise_orders.id"), nullable=False)
    merchandise_id = Column(Integer, ForeignKey("merchandise.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)  # Price at time of order
    total_price = Column(Float, nullable=False)  # quantity * unit_price
    selected_size = Column(String(50), nullable=True)  # e.g., "M"
    selected_color = Column(String(50), nullable=True)  # e.g., "Red"
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    order = relationship("MerchandiseOrder", back_populates="items")
    merchandise = relationship("Merchandise", back_populates="order_items")
