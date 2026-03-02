from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional
from app.database import get_db
from app.models.models import User, ClubMembershipRequest, TBLRMembership, MembershipStatus
from app.schemas.schemas import UserRegister, UserLogin, UserResponse, TokenResponse, SocialAuthLogin
from app.security import get_password_hash, verify_password, create_access_token, decode_access_token
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        phone=user_data.phone,
        password_hash=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse.from_orm(new_user)


@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user and return JWT token."""
    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
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


@router.post("/social-login", response_model=TokenResponse)
def social_login(auth_data: SocialAuthLogin, db: Session = Depends(get_db)):
    """
    Login or register user via social authentication (Google, Apple, Facebook).
    
    In a production environment, this should:
    1. Verify the token with the provider's API
    2. Extract user info from the token
    3. Create user if doesn't exist, or login existing user
    
    For now, this is a simplified implementation that trusts the token.
    """
    # TODO: In production, verify token with provider API
    # For Google: https://www.googleapis.com/oauth2/v3/tokeninfo?id_token={token}
    # For Apple: Verify JWT signature with Apple's public keys
    # For Facebook: https://graph.facebook.com/me?access_token={token}
    
    if not auth_data.email:
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
