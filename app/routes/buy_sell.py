from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.models import Listing, User, ListingStatus
from app.schemas.schemas import ListingCreate, ListingUpdate, ListingResponse
from app.routes.auth import get_current_user

router = APIRouter(prefix="/listings", tags=["buy-sell"])


@router.get("", response_model=List[ListingResponse])
def get_listings(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = "active",
    db: Session = Depends(get_db)
):
    """Get all active listings for browse."""
    query = db.query(Listing).filter(Listing.status == ListingStatus.ACTIVE)
    
    if status and status != "all":
        try:
            listing_status = ListingStatus(status)
            query = query.filter(Listing.status == listing_status)
        except ValueError:
            pass  # Invalid status, ignore filter
    
    listings = query.order_by(Listing.created_at.desc()).offset(skip).limit(limit).all()
    return listings


@router.get("/my", response_model=List[ListingResponse])
def get_my_listings(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's listings."""
    listings = db.query(Listing).filter(
        Listing.user_id == current_user.id
    ).order_by(Listing.created_at.desc()).offset(skip).limit(limit).all()
    
    return listings


@router.get("/{listing_id}", response_model=ListingResponse)
def get_listing(listing_id: int, db: Session = Depends(get_db)):
    """Get specific listing by ID."""
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )
    
    return listing


@router.post("", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
def create_listing(
    listing_data: ListingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new car listing."""
    new_listing = Listing(
        user_id=current_user.id,
        title=listing_data.title,
        description=listing_data.description,
        price=listing_data.price,
        year=listing_data.year,
        mileage=listing_data.mileage,
        location=listing_data.location,
        vehicle_model=listing_data.vehicle_model,
        vehicle_number=listing_data.vehicle_number,
        image_url=listing_data.image_url,
        status=ListingStatus.ACTIVE
    )
    
    db.add(new_listing)
    db.commit()
    db.refresh(new_listing)
    
    return new_listing


@router.patch("/{listing_id}", response_model=ListingResponse)
def update_listing(
    listing_id: int,
    listing_data: ListingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a listing (only by owner)."""
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )
    
    # Check if user owns this listing
    if listing.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own listings"
        )
    
    # Update fields
    update_data = listing_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "status" and value:
            try:
                setattr(listing, field, ListingStatus(value))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {value}"
                )
        else:
            setattr(listing, field, value)
    
    db.commit()
    db.refresh(listing)
    
    return listing


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_listing(
    listing_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a listing (only by owner) - soft delete by marking as deleted."""
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )
    
    # Check if user owns this listing
    if listing.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own listings"
        )
    
    # Soft delete
    listing.status = ListingStatus.DELETED
    db.commit()
    
    return None
