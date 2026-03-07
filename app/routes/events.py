from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
from typing import List, Optional
from app.database import get_db
from app.models.models import (
    User, Event, EventRegistration, CoPassenger, Payment, ClubMembershipRequest,
    EventStatus, EventDifficulty, RegistrationStatus, PaymentStatus,
    MembershipStatus
)
from app.schemas.schemas import (
    EventCreate, EventUpdate, EventResponse,
    EventRegistrationCreate, EventRegistrationResponse,
    CoPassengerResponse
)
from app.routes.auth import get_current_user
import hashlib
import secrets

router = APIRouter(prefix="/events", tags=["events"])


def check_admin(current_user: User):
    """UC005: Helper to verify admin role."""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )


def generate_whatsapp_link(event_id: int, user_id: int, registration_id: int) -> str:
    """
    UC005: Generate unique WhatsApp link for participant.
    In production, this would integrate with WhatsApp Business API.
    For now, generates a unique identifier that can be mapped to a group invite.
    """
    # Create unique hash for this participant
    unique_string = f"{event_id}-{user_id}-{registration_id}-{secrets.token_urlsafe(16)}"
    unique_hash = hashlib.sha256(unique_string.encode()).hexdigest()[:16]
    
    # In production, this would be a WhatsApp group invite link
    #return f"https://chat.whatsapp.com/{unique_hash}"
    
    # For development, return a placeholder that can be replaced later
    return f"whatsapp://chat?code={unique_hash}&event={event_id}"


@router.get("", response_model=List[EventResponse])
def list_events(
    status_filter: Optional[str] = "published",
    upcoming_only: bool = True,
    db: Session = Depends(get_db)
):
    """
    UC005: List events.
    Guests/members see only published, upcoming events.
    """
    query = db.query(Event)
    
    # Filter by status
    if status_filter:
        query = query.filter(Event.status == EventStatus.PUBLISHED)
    
    # Filter upcoming events only
    if upcoming_only:
        query = query.filter(Event.event_date >= datetime.utcnow())
    
    # Order by event date
    query = query.order_by(Event.event_date.asc())
    
    return query.all()


@router.get("/my-registrations", response_model=List[EventRegistrationResponse])
def get_my_registrations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """UC005: Get current user's event registrations."""
    registrations = db.query(EventRegistration).filter(
        EventRegistration.user_id == current_user.id
    ).order_by(EventRegistration.registered_at.desc()).all()

    return registrations


@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    """UC005: Get event details."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return event


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    event_data: EventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """UC005: Create event (admin only)."""
    check_admin(current_user)
    
    # Validate dates
    if event_data.registration_deadline >= event_data.event_date:
        raise HTTPException(
            status_code=400,
            detail="Registration deadline must be before event date"
        )
    
    # Create event
    new_event = Event(
        name=event_data.name,
        description=event_data.description,
        event_date=event_data.event_date,
        location=event_data.location,
        difficulty_level=EventDifficulty(event_data.difficulty_level),
        required_vehicle_type=event_data.required_vehicle_type,
        max_participants=event_data.max_participants,
        registration_deadline=event_data.registration_deadline,
        event_fee=event_data.event_fee,
        per_person_charge=event_data.per_person_charge,
        safety_requirements=event_data.safety_requirements,
        image_url=event_data.image_url,
        whatsapp_group_template=event_data.whatsapp_group_template,
        created_by=current_user.id,
        status=EventStatus.DRAFT
    )
    
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    
    return new_event


@router.patch("/{event_id}", response_model=EventResponse)
def update_event(
    event_id: int,
    event_data: EventUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """UC005: Update event (admin only)."""
    check_admin(current_user)
    
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Update fields
    for key, value in event_data.dict(exclude_unset=True).items():
        if value is not None:
            if key == "difficulty_level":
                setattr(event, key, EventDifficulty(value))
            elif key == "status":
                setattr(event, key, EventStatus(value))
            else:
                setattr(event, key, value)
    
    db.commit()
    db.refresh(event)
    
    return event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """UC005: Delete event (admin only)."""
    check_admin(current_user)
    
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    db.delete(event)
    db.commit()


@router.post("/{event_id}/register", response_model=EventRegistrationResponse, status_code=status.HTTP_201_CREATED)
def register_for_event(
    event_id: int,
    registration_data: EventRegistrationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    UC005: Register for event.
    Main success scenario implementation.
    """
    # Get event
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # UC005 A5: Check membership is active (approved membership request)
    club_membership = db.query(ClubMembershipRequest).filter(
        ClubMembershipRequest.user_id == current_user.id,
        ClubMembershipRequest.status == MembershipStatus.APPROVED
    ).order_by(ClubMembershipRequest.created_at.desc()).first()

    if not club_membership:
        raise HTTPException(
            status_code=403,
            detail="Active membership required to register for events"
        )
    
    # UC005 A8: Check event is enabled
    if event.status != EventStatus.PUBLISHED:
        raise HTTPException(
            status_code=400,
            detail="This event is no longer available"
        )
    
    # UC005 A7: Check registration deadline
    if datetime.utcnow() > event.registration_deadline:
        raise HTTPException(
            status_code=400,
            detail="Registration for this event is closed"
        )
    
    # UC005 A6: Check slot availability
    if event.current_participants >= event.max_participants:
        raise HTTPException(
            status_code=400,
            detail="Event registration limit reached"
        )
    
    # UC005: Prevent duplicate registrations
    existing = db.query(EventRegistration).filter(
        and_(
            EventRegistration.event_id == event_id,
            EventRegistration.user_id == current_user.id,
            EventRegistration.registration_status.in_([RegistrationStatus.PENDING, RegistrationStatus.CONFIRMED])
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=409,
            detail="You have already registered for this event"
        )
    
    # UC005 A1: Validate co-passenger details
    if registration_data.num_copassengers > 0:
        if len(registration_data.copassengers) != registration_data.num_copassengers:
            raise HTTPException(
                status_code=400,
                detail="Please enter co-passenger details before proceeding"
            )
    
    # UC005: Calculate total amount
    total_amount = event.event_fee + (registration_data.num_copassengers * event.per_person_charge)
    
    # Create registration (status: PENDING until payment)
    new_registration = EventRegistration(
        event_id=event_id,
        user_id=current_user.id,
        registration_status=RegistrationStatus.PENDING,
        num_copassengers=registration_data.num_copassengers,
        total_amount=total_amount
    )
    
    db.add(new_registration)
    db.flush()  # Get registration ID
    
    # Add co-passengers
    for cp_data in registration_data.copassengers:
        copassenger = CoPassenger(
            registration_id=new_registration.id,
            name=cp_data.name,
            age=cp_data.age,
            gender=cp_data.gender
        )
        db.add(copassenger)
    
    db.commit()
    db.refresh(new_registration)
    
    # Return registration with payment initiation needed
    return new_registration


@router.get("/{event_id}/registrations", response_model=List[EventRegistrationResponse])
def get_event_registrations(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """UC005: Get event registrations (admin only)."""
    check_admin(current_user)
    
    registrations = db.query(EventRegistration).filter(
        EventRegistration.event_id == event_id
    ).all()
    
    return registrations
