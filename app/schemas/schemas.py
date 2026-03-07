from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List


# ==================== AUTH SCHEMAS ====================
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    preferences: Optional[str] = None
    profile_photo: Optional[str] = None
    role: Optional[str] = None
    membership_status: Optional[str] = None
    tblr_membership_status: Optional[str] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class ProfileUpdate(BaseModel):
    """UC004A: Schema for updating user profile. Email and phone are locked."""
    name: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    preferences: Optional[str] = None
    profile_photo: Optional[str] = None


# ==================== FEED SCHEMAS ====================
class FeedCommentCreate(BaseModel):
    content: str


class FeedCommentResponse(BaseModel):
    id: int
    content: str
    author: UserResponse
    created_at: datetime
    
    class Config:
        from_attributes = True


class FeedCreate(BaseModel):
    title: str
    content: str
    image_url: Optional[str] = None


class FeedResponse(BaseModel):
    id: int
    title: str
    content: str
    image_url: Optional[str]
    likes_count: int
    author: UserResponse
    comments: List[FeedCommentResponse]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FeedListResponse(BaseModel):
    id: int
    title: str
    content: str
    image_url: Optional[str]
    likes_count: int
    author: UserResponse
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== ACCESSORY SCHEMAS ====================
class AccessoryCreate(BaseModel):
    name: str
    description: str
    category: str
    price: float
    image_url: Optional[str] = None
    stock: int


class AccessoryResponse(BaseModel):
    id: int
    name: str
    description: str
    category: str
    price: float
    image_url: Optional[str]
    stock: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ==================== MERCHANDISE SCHEMAS ====================
class MerchandiseCreate(BaseModel):
    name: str
    description: str
    price: float
    image_url: Optional[str] = None
    sizes: Optional[str] = None  # JSON string: '["S", "M", "L"]'
    colors: Optional[str] = None  # JSON string
    stock: int


class MerchandiseResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float
    image_url: Optional[str]
    sizes: Optional[str]
    colors: Optional[str]
    stock: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ==================== MEMBERSHIP SCHEMAS ====================
class ClubMembershipRequestCreate(BaseModel):
    name: str
    email: str
    phone: str
    vehicle_model: str
    vehicle_number: str
    registration_date: datetime
    reason: str


class ClubMembershipRequestResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    vehicle_model: str
    vehicle_number: str
    registration_date: datetime
    reason: str
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ==================== TBLR MEMBERSHIP SCHEMAS ====================
class TBLRMembershipCreate(BaseModel):
    full_name: str
    email: str
    phone: str
    vehicle_model: str
    vehicle_number: str
    experience_level: str
    motivation: str


class TBLRMembershipResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone: str
    vehicle_model: str
    vehicle_number: str
    experience_level: str
    motivation: str
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ==================== CART SCHEMAS ====================
class CartItemCreate(BaseModel):
    product_type: str  # "accessory" or "merchandise"
    product_id: int
    quantity: int
    size: Optional[str] = None
    color: Optional[str] = None


class CartItemResponse(BaseModel):
    id: int
    product_type: str
    product_id: int
    quantity: int
    size: Optional[str]
    color: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== SOCIAL AUTH SCHEMAS ====================
class SocialAuthLogin(BaseModel):
    provider: str  # "google", "apple", "facebook"
    token: str  # OAuth token from provider
    email: Optional[str] = None
    name: Optional[str] = None


# ==================== LISTING SCHEMAS ====================
class ListingCreate(BaseModel):
    title: str
    description: str
    price: float
    year: str
    mileage: str
    location: str
    vehicle_model: Optional[str] = None
    vehicle_number: Optional[str] = None
    image_url: Optional[str] = None


class ListingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    year: Optional[str] = None
    mileage: Optional[str] = None
    location: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_number: Optional[str] = None
    image_url: Optional[str] = None
    status: Optional[str] = None


class ListingResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: str
    price: float
    year: str
    mileage: str
    location: str
    vehicle_model: Optional[str]
    vehicle_number: Optional[str]
    image_url: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    seller: UserResponse
    
    class Config:
        from_attributes = True



# ==================== UC004B: EVENT REGISTRATION & PAYMENT SCHEMAS ====================

class CoPassengerCreate(BaseModel):
    name: str
    age: int
    gender: str  # Male, Female, Other


class CoPassengerResponse(BaseModel):
    id: int
    name: str
    age: int
    gender: str
    created_at: datetime

    class Config:
        from_attributes = True


class EventCreate(BaseModel):
    name: str
    description: str
    event_date: datetime
    location: str
    difficulty_level: str = "moderate"
    required_vehicle_type: Optional[str] = None
    max_participants: int
    registration_deadline: datetime
    event_fee: float
    per_person_charge: float = 0.0
    safety_requirements: Optional[str] = None
    image_url: Optional[str] = None
    whatsapp_group_template: Optional[str] = None


class EventUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    event_date: Optional[datetime] = None
    location: Optional[str] = None
    difficulty_level: Optional[str] = None
    required_vehicle_type: Optional[str] = None
    max_participants: Optional[int] = None
    registration_deadline: Optional[datetime] = None
    event_fee: Optional[float] = None
    per_person_charge: Optional[float] = None
    safety_requirements: Optional[str] = None
    status: Optional[str] = None
    image_url: Optional[str] = None


class EventResponse(BaseModel):
    id: int
    name: str
    description: str
    event_date: datetime
    location: str
    difficulty_level: str
    required_vehicle_type: Optional[str]
    max_participants: int
    current_participants: int
    registration_deadline: datetime
    event_fee: float
    per_person_charge: float
    safety_requirements: Optional[str]
    status: str
    image_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EventRegistrationCreate(BaseModel):
    """UC004B: Registration request with co-passengers."""
    num_copassengers: int = 0
    copassengers: List[CoPassengerCreate] = []


class EventRegistrationResponse(BaseModel):
    id: int
    event_id: int
    user_id: int
    registration_status: str
    num_copassengers: int
    total_amount: float
    whatsapp_link: Optional[str]
    confirmation_sent: bool
    registered_at: datetime
    copassengers: List[CoPassengerResponse]

    class Config:
        from_attributes = True


class PaymentInitiate(BaseModel):
    """UC004B: Request to initiate payment."""
    event_id: int
    registration_id: int
    amount: float
    payment_gateway: str = "razorpay"  # razorpay or phonepe


class PaymentResponse(BaseModel):
    id: int
    amount: float
    currency: str
    payment_gateway: str
    gateway_order_id: Optional[str]
    payment_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentVerify(BaseModel):
    """UC004B: Verify payment from gateway callback."""
    gateway_payment_id: str
    gateway_order_id: str
    gateway_signature: Optional[str] = None
