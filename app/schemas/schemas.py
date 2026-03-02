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
