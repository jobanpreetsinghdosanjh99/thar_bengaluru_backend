from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional
from app.database import get_db
from app.models.models import User, ClubMembershipRequest, TBLRMembership, MembershipStatus
from app.schemas.schemas import UserRegister, UserLogin, UserResponse, TokenResponse, SocialAuthLogin, ProfileUpdate
from app.security import get_password_hash, verify_password, create_access_token, decode_access_token
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user.
    UC003: New users must verify their email before they can login.
    """
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    # Create new user
    # UC003: email_verified defaults to False - user must verify email before login
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        phone=user_data.phone,
        password_hash=hashed_password,
        email_verified=False  # UC003: Must verify email before login
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse.from_orm(new_user)


@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login user and return JWT token. 
    Supports login by email or mobile number (UC003 requirement).
    Validates email verification and account ban status.
    """
    from datetime import datetime, timedelta as dt_timedelta
    
    # Find user by email or phone (mobile number)
    user = db.query(User).filter(
        (User.email == credentials.email) | (User.phone == credentials.email)
    ).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        # Track failed login attempts for cooldown (A2: Invalid Credentials)
        if user:
            user.failed_login_attempts += 1
            user.last_failed_login_at = datetime.utcnow()
            db.commit()
            # After 5 failed attempts, require cooldown of 15 minutes
            if user.failed_login_attempts >= 5:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many failed attempts. Please try again in 15 minutes."
                )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    # Check if login cooldown is active (15 minutes after 5 failed attempts)
    if user.failed_login_attempts >= 5 and user.last_failed_login_at:
        cooldown_time = user.last_failed_login_at + dt_timedelta(minutes=15)
        if datetime.utcnow() < cooldown_time:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed attempts. Please try again later."
            )
        else:
            # Cooldown expired, reset counter
            user.failed_login_attempts = 0
            user.last_failed_login_at = None
    
    # UC003: Check if user account is banned
    if user.is_banned:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account has been banned.")
    
    # UC003: Check if user's email is verified (A3: Unverified Email)
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Please verify your email before logging in. Check your email for verification link."
        )
    
    # Reset failed login attempts on successful login
    user.failed_login_attempts = 0
    user.last_failed_login_at = None
    db.commit()
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=access_token_expires
    )
    
    # Get membership statuses
    club_membership = db.query(ClubMembershipRequest).filter(
        ClubMembershipRequest.user_id == user.id,
        ClubMembershipRequest.status.in_([MembershipStatus.APPROVED, MembershipStatus.PENDING])
    ).order_by(ClubMembershipRequest.created_at.desc()).first()
    
    tblr_membership = db.query(TBLRMembership).filter(
        TBLRMembership.user_id == user.id,
        TBLRMembership.status.in_([MembershipStatus.APPROVED, MembershipStatus.PENDING])
    ).order_by(TBLRMembership.created_at.desc()).first()
    
    user_response = UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        role=user.role.value if user.role else "user",
        membership_status=club_membership.status.value if club_membership else None,
        tblr_membership_status=tblr_membership.status.value if tblr_membership else None,
        created_at=user.created_at
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_response
    }


def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> User:
    """Dependency to get current authenticated user from Bearer token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not authorization:
        raise credentials_exception
    
    # Extract token from "Bearer <token>"
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise credentials_exception
    except ValueError:
        raise credentials_exception
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    
    return user


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user info with membership statuses."""
    # Get membership statuses
    club_membership = db.query(ClubMembershipRequest).filter(
        ClubMembershipRequest.user_id == current_user.id,
        ClubMembershipRequest.status.in_([MembershipStatus.APPROVED, MembershipStatus.PENDING])
    ).order_by(ClubMembershipRequest.created_at.desc()).first()
    
    tblr_membership = db.query(TBLRMembership).filter(
        TBLRMembership.user_id == current_user.id,
        TBLRMembership.status.in_([MembershipStatus.APPROVED, MembershipStatus.PENDING])
    ).order_by(TBLRMembership.created_at.desc()).first()
    
    # Create response with membership statuses
    user_dict = {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "phone": current_user.phone,
        "role": current_user.role.value if current_user.role else "user",
        "membership_status": club_membership.status.value if club_membership else None,
        "tblr_membership_status": tblr_membership.status.value if tblr_membership else None,
        "created_at": current_user.created_at
    }
    
    return UserResponse(**user_dict)


@router.put("/me", response_model=UserResponse)
def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    UC004A: Update user profile.
    Only allows updating: name, address, emergency_contact, preferences, profile_photo.
    Email and phone are locked and can only be changed by admins.
    """
    # Update only the fields that are provided
    if profile_data.name is not None:
        current_user.name = profile_data.name
    if profile_data.address is not None:
        current_user.address = profile_data.address
    if profile_data.emergency_contact is not None:
        current_user.emergency_contact = profile_data.emergency_contact
    if profile_data.preferences is not None:
        current_user.preferences = profile_data.preferences
    if profile_data.profile_photo is not None:
        current_user.profile_photo = profile_data.profile_photo
    
    db.commit()
    db.refresh(current_user)
    
    # Get membership statuses (same as GET /me)
    from app.models.models import ClubMembershipRequest, TBLRMembership, MembershipStatus
    club_membership = db.query(ClubMembershipRequest).filter(
        ClubMembershipRequest.user_id == current_user.id,
        ClubMembershipRequest.status.in_([MembershipStatus.APPROVED, MembershipStatus.PENDING])
    ).order_by(ClubMembershipRequest.created_at.desc()).first()
    
    tblr_membership = db.query(TBLRMembership).filter(
        TBLRMembership.user_id == current_user.id,
        TBLRMembership.status.in_([MembershipStatus.APPROVED, MembershipStatus.PENDING])
    ).order_by(TBLRMembership.created_at.desc()).first()
    
    user_dict = {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "phone": current_user.phone,
        "address": current_user.address,
        "emergency_contact": current_user.emergency_contact,
        "preferences": current_user.preferences,
        "profile_photo": current_user.profile_photo,
        "role": current_user.role.value if current_user.role else "user",
        "membership_status": club_membership.status.value if club_membership else None,
        "tblr_membership_status": tblr_membership.status.value if tblr_membership else None,
        "created_at": current_user.created_at
    }
    
    return UserResponse(**user_dict)



@router.post("/social-login", response_model=TokenResponse)
def social_login(auth_data: SocialAuthLogin, db: Session = Depends(get_db)):
    """
    Login or register user via social authentication (Google, Apple, Facebook).
    
    This endpoint validates provider and token presence and then
    performs account lookup/creation for social authentication.
    """
    allowed_providers = {"google", "apple", "facebook"}
    provider = (auth_data.provider or "").strip().lower()

    if provider not in allowed_providers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported provider: {auth_data.provider}"
        )

    if not auth_data.token or not auth_data.token.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token is required for social authentication"
        )

    if not auth_data.email or not auth_data.email.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required for social authentication"
        )
    
    # Check if user exists
    user = db.query(User).filter(User.email == auth_data.email).first()
    
    if not user:
        # Create new user with social auth
        # Generate a random password since social auth doesn't use passwords
        import secrets
        random_password = secrets.token_urlsafe(32)
        
        user = User(
            name=auth_data.name or auth_data.email.split("@")[0],
            email=auth_data.email,
            password_hash=get_password_hash(random_password)  # User won't use this
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=access_token_expires
    )
    
    # Get membership statuses
    club_membership = db.query(ClubMembershipRequest).filter(
        ClubMembershipRequest.user_id == user.id,
        ClubMembershipRequest.status.in_([MembershipStatus.APPROVED, MembershipStatus.PENDING])
    ).order_by(ClubMembershipRequest.created_at.desc()).first()
    
    tblr_membership = db.query(TBLRMembership).filter(
        TBLRMembership.user_id == user.id,
        TBLRMembership.status.in_([MembershipStatus.APPROVED, MembershipStatus.PENDING])
    ).order_by(TBLRMembership.created_at.desc()).first()
    
    user_response = UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        role=user.role.value if user.role else "user",
        membership_status=club_membership.status.value if club_membership else None,
        tblr_membership_status=tblr_membership.status.value if tblr_membership else None,
        created_at=user.created_at
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_response
    }

# ============================================================
# UC003: Email Verification & Password Reset Flows
# ============================================================

@router.post("/send-email-verification-otp")
def send_email_verification_otp(request_data: dict, db: Session = Depends(get_db)):
    """
    UC003 A3: Send email verification OTP to user''s email.
    Required for users to verify their email before first login.
    """
    email = request_data.get("email", "").strip().lower()
    
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is required")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # If already verified, no need to send OTP
    if user.email_verified:
        return {"message": "Email already verified"}
    
    # Generate 6-digit OTP
    import random
    otp = str(random.randint(100000, 999999))
    
    # Store OTP with 10-minute expiry
    from datetime import datetime, timedelta as dt_timedelta
    user.email_verification_otp = otp
    user.email_verification_otp_expires_at = datetime.utcnow() + dt_timedelta(minutes=10)
    db.commit()
    
    # Development transport: OTP is emitted to server logs.
    print(f"[EMAIL SERVICE] Verification OTP for {email}: {otp}")
    
    return {
        "message": "OTP sent to your email",
        "expires_in_minutes": 10,
    }


@router.post("/verify-email-otp")
def verify_email_otp(request_data: dict, db: Session = Depends(get_db)):
    """
    UC003 A3: Verify email OTP and mark email as verified.
    User must complete this before login is allowed.
    """
    email = request_data.get("email", "").strip().lower()
    otp = request_data.get("otp", "").strip()
    
    if not email or not otp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email and OTP are required")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Check if OTP exists and is not expired
    if not user.email_verification_otp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No OTP request found. Send verification OTP first.")
    
    from datetime import datetime
    if datetime.utcnow() > user.email_verification_otp_expires_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP expired. Request a new one.")
    
    # Verify OTP
    if user.email_verification_otp != otp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")
    
    # Mark email as verified
    user.email_verified = True
    user.email_verification_otp = None
    user.email_verification_otp_expires_at = None
    db.commit()
    
    return {"message": "Email verified successfully. You can now login."}


@router.post("/forgot-password")
def forgot_password(request_data: dict, db: Session = Depends(get_db)):
    """
    UC003 A1: Send password reset OTP to user''s email.
    User provides email, receives OTP to reset password.
    """
    email = request_data.get("email", "").strip().lower()
    
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is required")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Generate 6-digit OTP
    import random
    otp = str(random.randint(100000, 999999))
    
    # Store OTP with 10-minute expiry
    from datetime import datetime, timedelta as dt_timedelta
    user.password_reset_otp = otp
    user.password_reset_otp_expires_at = datetime.utcnow() + dt_timedelta(minutes=10)
    db.commit()
    
    # Development transport: OTP is emitted to server logs.
    print(f"[EMAIL SERVICE] Password Reset OTP for {email}: {otp}")
    
    return {
        "message": "Password reset OTP sent to your email",
        "expires_in_minutes": 10,
    }


@router.post("/reset-password")
def reset_password(request_data: dict, db: Session = Depends(get_db)):
    """
    UC003 A1: Verify OTP and reset password.
    User provides email, OTP, and new password.
    """
    email = request_data.get("email", "").strip().lower()
    otp = request_data.get("otp", "").strip()
    new_password = request_data.get("new_password", "")
    
    if not email or not otp or not new_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email, OTP, and new password are required")
    
    if len(new_password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 6 characters")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Check if OTP exists and is not expired
    if not user.password_reset_otp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No password reset request found. Request OTP first.")
    
    from datetime import datetime
    if datetime.utcnow() > user.password_reset_otp_expires_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP expired. Request a new one.")
    
    # Verify OTP
    if user.password_reset_otp != otp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")
    
    # Update password
    user.password_hash = get_password_hash(new_password)
    user.password_reset_otp = None
    user.password_reset_otp_expires_at = None
    db.commit()
    
    return {"message": "Password reset successfully. You can now login with your new password."}
