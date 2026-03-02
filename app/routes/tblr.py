from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.models import TBLRMembership, User, UserRole, MembershipStatus
from app.schemas.schemas import TBLRMembershipCreate, TBLRMembershipResponse
from app.routes.auth import get_current_user

router = APIRouter(prefix="/memberships/tblr-applications", tags=["tblr"])


@router.post("", response_model=TBLRMembershipResponse)
def submit_tblr_application(
    app_data: TBLRMembershipCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit TBLR membership application."""
    new_app = TBLRMembership(
        user_id=current_user.id,
        full_name=app_data.full_name,
        email=app_data.email,
        phone=app_data.phone,
        vehicle_model=app_data.vehicle_model,
        vehicle_number=app_data.vehicle_number,
        experience_level=app_data.experience_level,
        motivation=app_data.motivation
    )
    db.add(new_app)
    db.commit()
    db.refresh(new_app)
    return new_app


@router.get("", response_model=List[TBLRMembershipResponse])
def list_tblr_applications(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of TBLR applications. Admins see all, users see only their own."""
    if current_user.role == UserRole.ADMIN:
        # Admins can see all applications
        apps = db.query(TBLRMembership).offset(skip).limit(limit).all()
    else:
        # Regular users see only their own applications
        apps = db.query(TBLRMembership).filter(
            TBLRMembership.user_id == current_user.id
        ).offset(skip).limit(limit).all()
    return apps


@router.get("/{app_id}", response_model=TBLRMembershipResponse)
def get_tblr_application(
    app_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get single TBLR application for current user."""
    app = db.query(TBLRMembership).filter(
        TBLRMembership.id == app_id,
        TBLRMembership.user_id == current_user.id
    ).first()
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return app


@router.patch("/{app_id}/approve", response_model=TBLRMembershipResponse)
def approve_tblr_application(
    app_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Approve TBLR application (admin only)."""
    # Check admin role
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    app = db.query(TBLRMembership).filter(TBLRMembership.id == app_id).first()
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    
    if app.status != MembershipStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve application with status: {app.status.value}"
        )
    
    app.status = MembershipStatus.APPROVED
    db.commit()
    db.refresh(app)
    return app


@router.patch("/{app_id}/reject", response_model=TBLRMembershipResponse)
def reject_tblr_application(
    app_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reject TBLR application (admin only)."""
    # Check admin role
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    app = db.query(TBLRMembership).filter(TBLRMembership.id == app_id).first()
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    
    if app.status != MembershipStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reject application with status: {app.status.value}"
        )
    
    app.status = MembershipStatus.REJECTED
    db.commit()
    db.refresh(app)
    return app
