from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.models import ClubMembershipRequest, MembershipStatus, User, UserRole
from app.schemas.schemas import ClubMembershipRequestCreate, ClubMembershipRequestResponse
from app.routes.auth import get_current_user

router = APIRouter(prefix="/memberships/club-requests", tags=["membership"])


@router.post("", response_model=ClubMembershipRequestResponse)
def submit_membership_request(
    request_data: ClubMembershipRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit a club membership request."""
    existing_pending = db.query(ClubMembershipRequest).filter(
        ClubMembershipRequest.user_id == current_user.id,
        ClubMembershipRequest.status == MembershipStatus.PENDING
    ).first()
    if existing_pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have a pending membership request."
        )

    existing_approved = db.query(ClubMembershipRequest).filter(
        ClubMembershipRequest.user_id == current_user.id,
        ClubMembershipRequest.status == MembershipStatus.APPROVED
    ).first()
    if existing_approved:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You are already an active Thar Bengaluru member."
        )

    new_request = ClubMembershipRequest(
        user_id=current_user.id,
        name=request_data.name,
        email=request_data.email,
        phone=request_data.phone,
        vehicle_model=request_data.vehicle_model,
        vehicle_number=request_data.vehicle_number,
        registration_date=request_data.registration_date,
        reason=request_data.reason
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    return new_request


@router.get("", response_model=List[ClubMembershipRequestResponse])
def list_membership_requests(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of membership requests. Admins see all, users see only their own."""
    if current_user.role == UserRole.ADMIN:
        # Admins can see all requests
        requests = db.query(ClubMembershipRequest).offset(skip).limit(limit).all()
    else:
        # Regular users see only their own requests
        requests = db.query(ClubMembershipRequest).filter(
            ClubMembershipRequest.user_id == current_user.id
        ).offset(skip).limit(limit).all()
    return requests


@router.get("/{request_id}", response_model=ClubMembershipRequestResponse)
def get_membership_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get single membership request for current user."""
    request_obj = db.query(ClubMembershipRequest).filter(
        ClubMembershipRequest.id == request_id,
        ClubMembershipRequest.user_id == current_user.id
    ).first()
    if not request_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    return request_obj


@router.patch("/{request_id}/approve", response_model=ClubMembershipRequestResponse)
def approve_membership_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Approve a membership request (admin only)."""
    # Check admin role
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    request_obj = db.query(ClubMembershipRequest).filter(
        ClubMembershipRequest.id == request_id
    ).first()
    if not request_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    
    if request_obj.status != MembershipStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve request with status: {request_obj.status.value}"
        )
    
    request_obj.status = MembershipStatus.APPROVED
    db.commit()
    db.refresh(request_obj)
    return request_obj


@router.patch("/{request_id}/reject", response_model=ClubMembershipRequestResponse)
def reject_membership_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reject a membership request (admin only)."""
    # Check admin role
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    request_obj = db.query(ClubMembershipRequest).filter(
        ClubMembershipRequest.id == request_id
    ).first()
    if not request_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    
    if request_obj.status != MembershipStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reject request with status: {request_obj.status.value}"
        )
    
    request_obj.status = MembershipStatus.REJECTED
    db.commit()
    db.refresh(request_obj)
    return request_obj
