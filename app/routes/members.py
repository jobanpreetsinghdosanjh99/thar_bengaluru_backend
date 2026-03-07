from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User, Vehicle, Message
from app.routes.auth import get_current_user

router = APIRouter(prefix="/members", tags=["members"])


# ==================== Member Discovery / Directory ====================

@router.get("", response_model=list)
def list_members(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    location: str = Query(None),
    role: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of members for member discovery with optional filters."""
    if current_user.is_banned:
        raise HTTPException(status_code=403, detail="Your account is banned")
    
    query = db.query(User).filter(User.id != current_user.id)
    
    # Filter by role if provided
    if role and role in ["user", "admin"]:
        from app.models.models import UserRole
        query = query.filter(User.role == role)
    
    # Pagination
    members = query.offset(skip).limit(limit).all()
    
    return [
        {
            "id": m.id,
            "name": m.name,
            "email": m.email,
            "phone": m.phone,
            "role": m.role.value if m.role else "user",
            "vehicles": [
                {
                    "make": v.make,
                    "model": v.model,
                    "year": v.year,
                    "registration_number": v.registration_number,
                }
                for v in m.vehicles
            ],
            "created_at": m.created_at,
        }
        for m in members
    ]


@router.get("/{member_id}", response_model=dict)
def get_member_profile(
    member_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed profile of a specific member."""
    if current_user.is_banned:
        raise HTTPException(status_code=403, detail="Your account is banned")
    
    member = db.query(User).filter(User.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    return {
        "id": member.id,
        "name": member.name,
        "email": member.email,
        "phone": member.phone,
        "role": member.role.value if member.role else "user",
        "vehicles": [
            {
                "id": v.id,
                "make": v.make,
                "model": v.model,
                "year": v.year,
                "registration_number": v.registration_number,
                "color": v.color,
                "is_primary": v.is_primary,
            }
            for v in member.vehicles
        ],
        "created_at": member.created_at,
    }


# ==================== Vehicle Management ====================

@router.post("/vehicles", response_model=dict)
def add_vehicle(
    vehicle_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a new vehicle to user's profile."""
    try:
        vehicle = Vehicle(
            user_id=current_user.id,
            make=vehicle_data.get("make"),
            model=vehicle_data.get("model"),
            year=vehicle_data.get("year"),
            registration_number=vehicle_data.get("registration_number"),
            color=vehicle_data.get("color"),
            mileage=vehicle_data.get("mileage"),
            is_primary=vehicle_data.get("is_primary", False)
        )
        db.add(vehicle)
        db.commit()
        db.refresh(vehicle)
        return {
            "id": vehicle.id,
            "make": vehicle.make,
            "model": vehicle.model,
            "year": vehicle.year,
            "registration_number": vehicle.registration_number,
            "is_primary": vehicle.is_primary,
            "created_at": vehicle.created_at,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to add vehicle: {str(e)}")


@router.get("/vehicles/user", response_model=list)
def get_user_vehicles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all vehicles for current user."""
    vehicles = db.query(Vehicle).filter(Vehicle.user_id == current_user.id).all()
    return [
        {
            "id": v.id,
            "make": v.make,
            "model": v.model,
            "year": v.year,
            "registration_number": v.registration_number,
            "color": v.color,
            "mileage": v.mileage,
            "is_primary": v.is_primary,
            "created_at": v.created_at,
        }
        for v in vehicles
    ]


@router.put("/vehicles/{vehicle_id}", response_model=dict)
def update_vehicle(
    vehicle_id: int,
    vehicle_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update vehicle details."""
    vehicle = db.query(Vehicle).filter(
        Vehicle.id == vehicle_id,
        Vehicle.user_id == current_user.id
    ).first()
    
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    try:
        if "make" in vehicle_data:
            vehicle.make = vehicle_data["make"]
        if "model" in vehicle_data:
            vehicle.model = vehicle_data["model"]
        if "year" in vehicle_data:
            vehicle.year = vehicle_data["year"]
        if "registration_number" in vehicle_data:
            vehicle.registration_number = vehicle_data["registration_number"]
        if "color" in vehicle_data:
            vehicle.color = vehicle_data["color"]
        if "mileage" in vehicle_data:
            vehicle.mileage = vehicle_data["mileage"]
        if "is_primary" in vehicle_data:
            vehicle.is_primary = vehicle_data["is_primary"]
        
        db.commit()
        db.refresh(vehicle)
        return {
            "id": vehicle.id,
            "make": vehicle.make,
            "model": vehicle.model,
            "year": vehicle.year,
            "registration_number": vehicle.registration_number,
            "is_primary": vehicle.is_primary,
            "updated_at": vehicle.updated_at,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to update vehicle: {str(e)}")


@router.delete("/vehicles/{vehicle_id}", status_code=204)
def delete_vehicle(
    vehicle_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a vehicle."""
    vehicle = db.query(Vehicle).filter(
        Vehicle.id == vehicle_id,
        Vehicle.user_id == current_user.id
    ).first()
    
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    db.delete(vehicle)
    db.commit()
    return None

