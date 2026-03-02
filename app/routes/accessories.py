from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.models import Accessory
from app.schemas.schemas import AccessoryCreate, AccessoryResponse

router = APIRouter(prefix="/accessories", tags=["accessories"])


@router.post("", response_model=AccessoryResponse)
def create_accessory(accessory_data: AccessoryCreate, db: Session = Depends(get_db)):
    """Create a new accessory (admin only in production)."""
    new_accessory = Accessory(
        name=accessory_data.name,
        description=accessory_data.description,
        category=accessory_data.category,
        price=accessory_data.price,
        image_url=accessory_data.image_url,
        stock=accessory_data.stock
    )
    db.add(new_accessory)
    db.commit()
    db.refresh(new_accessory)
    return new_accessory


@router.get("", response_model=List[AccessoryResponse])
def list_accessories(category: str = None, skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """Get list of accessories, optionally filtered by category."""
    query = db.query(Accessory)
    if category:
        query = query.filter(Accessory.category == category)
    accessories = query.offset(skip).limit(limit).all()
    return accessories


@router.get("/{accessory_id}", response_model=AccessoryResponse)
def get_accessory(accessory_id: int, db: Session = Depends(get_db)):
    """Get single accessory details."""
    accessory = db.query(Accessory).filter(Accessory.id == accessory_id).first()
    if not accessory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accessory not found")
    return accessory
