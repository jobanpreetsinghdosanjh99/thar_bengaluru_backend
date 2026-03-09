from pydantic import BaseModel, EmailStr, Field
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
    image_url: Optional[str] = None
    stock: int
    # UC004D: Vendor integration fields
    vendor_id: Optional[int] = None
    long_description: Optional[str] = None
    images: Optional[str] = None  # JSON string
    features: Optional[str] = None  # JSON string
    compatibility: Optional[str] = None
    brand: Optional[str] = None
    rating: float | None = Field(default=None)
    reviews_count: int | None = Field(default=None)
    is_featured: bool | None = Field(default=None)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ==================== MERCHANDISE SCHEMAS ====================
class MerchandiseCreate(BaseModel):
    vendor_id: int
    name: str
    description: str
    long_description: Optional[str] = None
    category: str  # "Apparel", "Stickers", "Accessories", etc.
    price: float
    image_url: Optional[str] = None
    images: Optional[str] = None  # JSON string: '["url1", "url2"]'
    sizes: Optional[str] = None  # JSON string: '[{"id": "m", "size": "M", "label": "Medium"}]'
    colors: Optional[str] = None  # JSON string: '[{"id": "red", "name": "Red", "hex": "#FF0000"}]'
    stock: int
    features: Optional[str] = None  # JSON string: '["Feature 1", "Feature 2"]'
    material: Optional[str] = None
    brand: Optional[str] = None
    rating: Optional[float] = 0.0
    reviews: Optional[int] = 0
    is_featured: Optional[bool] = False
    is_on_sale: Optional[bool] = False
    discounted_price: Optional[float] = None


class MerchandiseResponse(BaseModel):
    id: int
    vendor_id: Optional[int] = None
    name: str
    description: str
    long_description: Optional[str] = None
    category: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    images: Optional[str] = None
    sizes: Optional[str] = None
    colors: Optional[str] = None
    stock: int
    features: Optional[str] = None
    material: Optional[str] = None
    brand: Optional[str] = None
    rating: Optional[float] = 0.0
    reviews: Optional[int] = 0
    is_featured: Optional[bool] = False
    is_on_sale: Optional[bool] = False
    discounted_price: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    vendor: Optional[dict] = None  # Vendor details if joined
    
    class Config:
        from_attributes = True


class MerchandiseDetailResponse(BaseModel):
    """Detailed merchandise response with vendor info."""
    id: int
    vendor_id: Optional[int] = None
    name: str
    description: str
    long_description: Optional[str] = None
    category: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    images: Optional[str] = None
    sizes: Optional[str] = None
    colors: Optional[str] = None
    stock: int
    features: Optional[str] = None
    material: Optional[str] = None
    brand: Optional[str] = None
    rating: Optional[float] = 0.0
    reviews: Optional[int] = 0
    is_featured: Optional[bool] = False
    is_on_sale: Optional[bool] = False
    discounted_price: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    vendor: Optional[dict] = None
    
    class Config:
        from_attributes = True


# UC004E: Merchandise Checkout & Orders
class MerchandiseCartItemCreate(BaseModel):
    """Item in merchandise cart for checkout."""
    merchandise_id: int
    quantity: int
    size: Optional[str] = None
    color: Optional[str] = None


class MerchandiseCheckout(BaseModel):
    """Request to checkout merchandise order."""
    items: List[MerchandiseCartItemCreate]
    customer_name: str
    customer_email: str
    customer_phone: str
    shipping_address: str
    notes: Optional[str] = None


class MerchandiseOrderItemResponse(BaseModel):
    """Individual merchandise item in an order."""
    id: int
    merchandise_id: int
    quantity: int
    unit_price: float
    total_price: float
    selected_size: Optional[str] = None
    selected_color: Optional[str] = None
    merchandise: Optional[MerchandiseResponse] = None
    
    class Config:
        from_attributes = True


class MerchandiseOrderResponse(BaseModel):
    """Merchandise order details."""
    id: int
    order_number: str
    customer_name: str
    customer_email: str
    customer_phone: str
    shipping_address: str
    total_amount: float
    currency: str
    payment_gateway: str
    payment_status: str
    order_status: str
    vendor_notification_sent: bool
    user_confirmation_sent: bool
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[MerchandiseOrderItemResponse] = []
    vendor: Optional[dict] = None
    
    class Config:
        from_attributes = True


class MerchandiseOrderPaymentRedirect(BaseModel):
    """Response after initiating merchandise order payment."""
    order_id: int
    order_number: str
    payment_url: str
    payment_gateway: str
    gateway_order_id: Optional[str] = None
    amount: float
    currency: str


# ==================== MEMBERSHIP SCHEMAS ====================
class ClubMembershipRequestCreate(BaseModel):
    name: str
    email: str
    phone: str
    vehicle_model: str
    vehicle_number: str
    registration_date: datetime
    reason: str

    # UC005: additional profile and document fields
    residential_address: Optional[str] = None
    emergency_contact: Optional[str] = None
    vehicle_fuel_type: Optional[str] = None
    vehicle_transmission_type: Optional[str] = None
    profile_photo_url: Optional[str] = None
    rc_document_url: Optional[str] = None
    insurance_document_url: Optional[str] = None
    aadhaar_document_url: Optional[str] = None
    driving_license_document_url: Optional[str] = None
    vehicle_modifications: Optional[str] = None
    additional_info: Optional[str] = None
    terms_accepted: bool = False


class ClubMembershipAutofillResponse(BaseModel):
    tb_member_id: str
    first_name: str
    last_name: str
    mobile_number: str
    email_address: str
    residential_address: Optional[str] = None
    emergency_contact: Optional[str] = None
    vehicle_make_model: Optional[str] = None
    vehicle_fuel_type: Optional[str] = None
    vehicle_transmission_type: Optional[str] = None
    vehicle_registration_number: Optional[str] = None
    profile_photo_url: Optional[str] = None
    rc_document_url: Optional[str] = None


class ClubMembershipEligibilityResponse(BaseModel):
    eligible: bool
    reasons: List[str] = []
    workshop_trail_completed: bool
    membership_window_open: bool
    has_existing_membership: bool
    has_pending_request: bool


class ClubMembershipPaymentResponse(BaseModel):
    request_id: int
    payment_status: str
    payment_gateway: Optional[str] = None
    payment_order_id: Optional[str] = None
    payment_url: Optional[str] = None
    message: str


class ClubMembershipActivationResponse(BaseModel):
    request_id: int
    membership_id: Optional[str] = None
    membership_status: str
    whatsapp_group_name: Optional[str] = None
    whatsapp_group_link: Optional[str] = None
    whatsapp_join_available: bool = False
    message: str


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
    payment_status: Optional[str] = None
    payment_link_enabled: Optional[bool] = None
    membership_id: Optional[str] = None
    whatsapp_group_name: Optional[str] = None
    whatsapp_group_link: Optional[str] = None
    whatsapp_join_available: Optional[bool] = None
    rejection_reason: Optional[str] = None
    residential_address: Optional[str] = None
    emergency_contact: Optional[str] = None
    vehicle_fuel_type: Optional[str] = None
    vehicle_transmission_type: Optional[str] = None
    terms_accepted: Optional[bool] = None
    workshop_trail_completed: Optional[bool] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ==================== UC006: THAR BENGALURU MEMBERSHIP SCHEMAS ====================
class TharBengaluruMembershipCreate(BaseModel):
    first_name: str
    last_name: str
    mobile_number: str
    email_address: str
    residential_address: str
    emergency_contact: str
    vehicle_make: str = "Mahindra"
    vehicle_model: str
    vehicle_fuel_type: str
    vehicle_transmission_type: str
    vehicle_registration_number: str
    profile_photo_url: str
    rc_document_url: str
    insurance_document_url: Optional[str] = None
    aadhaar_document_url: str
    driving_license_document_url: str
    vehicle_modifications: Optional[str] = None
    additional_info: Optional[str] = None
    terms_accepted: bool = False


class TharBengaluruMembershipResponse(BaseModel):
    id: int
    user_id: int
    first_name: str
    last_name: str
    mobile_number: str
    email_address: str
    residential_address: str
    emergency_contact: str
    vehicle_make: str
    vehicle_model: str
    vehicle_fuel_type: str
    vehicle_transmission_type: str
    vehicle_registration_number: str
    profile_photo_url: str
    rc_document_url: str
    insurance_document_url: Optional[str] = None
    aadhaar_document_url: str
    driving_license_document_url: str
    vehicle_modifications: Optional[str] = None
    additional_info: Optional[str] = None
    status: str
    payment_status: Optional[str] = None
    payment_link_enabled: Optional[bool] = None
    membership_id: Optional[str] = None
    whatsapp_group_name: Optional[str] = None
    whatsapp_group_link: Optional[str] = None
    whatsapp_join_available: Optional[bool] = None
    rejection_reason: Optional[str] = None
    terms_accepted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TharBengaluruMembershipEligibilityResponse(BaseModel):
    eligible: bool
    reasons: List[str] = []
    workshop_trail_completed: bool
    has_existing_membership: bool
    has_pending_request: bool


class TharBengaluruMembershipAutofillResponse(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    mobile_number: Optional[str] = None
    email_address: Optional[str] = None
    residential_address: Optional[str] = None
    emergency_contact: Optional[str] = None
    vehicle_make: str = "Mahindra"
    vehicle_model: Optional[str] = None
    vehicle_registration_number: Optional[str] = None
    profile_photo_url: Optional[str] = None


class TharBengaluruMembershipPaymentResponse(BaseModel):
    request_id: int
    payment_status: str
    payment_gateway: Optional[str] = None
    payment_order_id: Optional[str] = None
    payment_url: Optional[str] = None
    message: str


class TharBengaluruMembershipActivationResponse(BaseModel):
    request_id: int
    membership_id: Optional[str] = None
    membership_status: str
    whatsapp_group_name: Optional[str] = None
    whatsapp_group_link: Optional[str] = None
    whatsapp_join_available: bool = False
    message: str


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


# ==================== UC004D: ACCESSORIES SHOPPING & VENDOR INTEGRATION SCHEMAS ====================

class VendorResponse(BaseModel):
    """Vendor information for order summaries."""
    id: int
    name: str
    email: str
    whatsapp_number: str
    payment_gateway: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class AccessoryDetailResponse(BaseModel):
    """Enhanced accessory response with vendor details."""
    id: int
    vendor_id: Optional[int] = None
    name: str
    description: str
    long_description: Optional[str] = None
    category: str
    price: float
    image_url: Optional[str] = None
    images: Optional[str]  # JSON list
    stock: int
    features: Optional[str]  # JSON list
    compatibility: Optional[str] = None
    brand: Optional[str] = None
    rating: float | None = Field(default=None)
    reviews_count: int | None = Field(default=None)
    is_featured: bool | None = Field(default=None)
    vendor: Optional[VendorResponse] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AccessoryOrderItemResponse(BaseModel):
    """Item in an accessory order."""
    id: int
    accessory_id: int
    quantity: int
    unit_price: float
    total_price: float
    accessory: Optional[AccessoryDetailResponse] = None
    
    class Config:
        from_attributes = True


class AccessoryCheckout(BaseModel):
    """Request to checkout accessories from cart."""
    items: List[CartItemCreate]  # Cart items to purchase
    customer_name: str
    customer_email: str
    customer_phone: str
    shipping_address: str


class AccessoryOrderResponse(BaseModel):
    """Complete order response."""
    id: int
    order_number: str
    customer_name: str
    customer_email: str
    customer_phone: str
    shipping_address: str
    total_amount: float
    currency: str
    payment_gateway: str
    payment_id: Optional[str]
    order_id: Optional[str]
    payment_status: str
    order_status: str
    vendor_notification_sent: bool
    vendor: VendorResponse
    items: List[AccessoryOrderItemResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AccessoryOrderPaymentRedirect(BaseModel):
    """Response with vendor payment gateway redirect URL."""
    order_id: int
    order_number: str
    gateway_redirect_url: str
    payment_id: Optional[str] = None
    amount: float
    currency: str


class PaymentVerify(BaseModel):
    """UC004B: Verify payment from gateway callback."""
    gateway_payment_id: str
    gateway_order_id: str
    gateway_signature: Optional[str] = None
