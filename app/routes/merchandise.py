from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.models import Merchandise
from app.schemas.schemas import MerchandiseCreate, MerchandiseResponse

router = APIRouter(prefix="/merchandise", tags=["merchandise"])


@router.post("", response_model=MerchandiseResponse)
def create_merchandise(merch_data: MerchandiseCreate, db: Session = Depends(get_db)):
    """Create a new merchandise item (admin only in production)."""
    new_merchandise = Merchandise(
        name=merch_data.name,
        description=merch_data.description,
        price=merch_data.price,
        image_url=merch_data.image_url,
        sizes=merch_data.sizes,
        colors=merch_data.colors,
        stock=merch_data.stock
    )
    db.add(new_merchandise)
    db.commit()
    db.refresh(new_merchandise)
    return new_merchandise


@router.get("", response_model=List[MerchandiseResponse])
def list_merchandise(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """Get list of merchandise."""
    merchandise = db.query(Merchandise).offset(skip).limit(limit).all()
    return merchandise


@router.get("/{merch_id}", response_model=MerchandiseResponse)
def get_merchandise(merch_id: int, db: Session = Depends(get_db)):
    """Get single merchandise details."""
    merchandise = db.query(Merchandise).filter(Merchandise.id == merch_id).first()
    if not merchandise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchandise not found")
    return merchandise
