from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import os
import hashlib
import hmac
from app.database import get_db
from app.models.models import (
    User, Event, EventRegistration, Payment,
    RegistrationStatus, PaymentStatus, EventStatus
)
from app.schemas.schemas import (
    PaymentInitiate, PaymentResponse, PaymentVerify
)
from app.routes.auth import get_current_user

router = APIRouter(prefix="/payments", tags=["payments"])

# Payment gateway credentials (load from environment)
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")


def generate_whatsapp_link(event_id: int, user_id: int, registration_id: int) -> str:
    """
    UC005: Generate unique WhatsApp link for participant.
    This is a placeholder - in production, integrate with WhatsApp Business API.
    """
    import secrets
    unique_string = f"{event_id}-{user_id}-{registration_id}-{secrets.token_urlsafe(16)}"
    unique_hash = hashlib.sha256(unique_string.encode()).hexdigest()[:16]
    return f"whatsapp://chat?code={unique_hash}&event={event_id}"


@router.post("/initiate", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def initiate_payment(
    payment_data: PaymentInitiate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    UC005 A2: Initiate payment for event registration.
    Creates payment order with gateway (Razorpay/PhonePe).
    """
    # Get registration
    registration = db.query(EventRegistration).filter(
        EventRegistration.id == payment_data.registration_id
    ).first()
    
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")
    
    # Verify ownership
    if registration.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check if already paid
    if registration.payment and registration.payment.payment_status == PaymentStatus.SUCCESS:
        raise HTTPException(status_code=400, detail="Payment already completed")
    
    # Get event
    event = db.query(Event).filter(Event.id == payment_data.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Verify amount matches
    if payment_data.amount != registration.total_amount:
        raise HTTPException(status_code=400, detail="Payment amount mismatch")
    
    # Create payment record
    new_payment = Payment(
        user_id=current_user.id,
        event_id=payment_data.event_id,
        amount=payment_data.amount,
        currency="INR",
        payment_gateway=payment_data.payment_gateway,
        payment_status=PaymentStatus.PENDING
    )
    
    db.add(new_payment)
    db.flush()  # Get payment ID
    
    # In production, create order with Razorpay/PhonePe
    # For now, generate mock order ID
    if payment_data.payment_gateway == "razorpay":
        # Production code:
        # import razorpay
        # client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
        # order = client.order.create({
        #     "amount": int(payment_data.amount * 100),  # Convert to paise
        #     "currency": "INR",
        #     "receipt": f"event_{payment_data.event_id}_reg_{payment_data.registration_id}"
        # })
        # new_payment.gateway_order_id = order["id"]
        
        # Mock for development
        new_payment.gateway_order_id = f"order_mock_{new_payment.id}_{datetime.utcnow().timestamp()}"
        
    elif payment_data.payment_gateway == "phonepe":
        # Similar PhonePe integration would go here
        new_payment.gateway_order_id = f"phonepe_mock_{new_payment.id}_{datetime.utcnow().timestamp()}"
    
    else:
        raise HTTPException(status_code=400, detail="Unsupported payment gateway")
    
    # Link payment to registration
    registration.payment_id = new_payment.id
    
    db.commit()
    db.refresh(new_payment)
    
    return new_payment


@router.post("/verify", response_model=PaymentResponse)
def verify_payment(
    verify_data: PaymentVerify,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    UC005 A3: Verify payment after gateway callback.
    Confirms payment signature and updates registration status.
    """
    # Find payment by gateway order ID
    payment = db.query(Payment).filter(
        Payment.gateway_order_id == verify_data.gateway_order_id
    ).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Verify ownership
    if payment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Verify signature (Razorpay example)
    if payment.payment_gateway == "razorpay":
        # Production signature verification:
        # generated_signature = hmac.new(
        #     RAZORPAY_KEY_SECRET.encode(),
        #     f"{verify_data.gateway_order_id}|{verify_data.gateway_payment_id}".encode(),
        #     hashlib.sha256
        # ).hexdigest()
        # 
        # if generated_signature != verify_data.gateway_signature:
        #     payment.payment_status = PaymentStatus.FAILED
        #     payment.failure_reason = "Signature verification failed"
        #     db.commit()
        #     raise HTTPException(status_code=400, detail="Invalid payment signature")
        
        # Mock verification (accept all in development)
        pass
    
    # Update payment status
    payment.gateway_payment_id = verify_data.gateway_payment_id
    payment.payment_status = PaymentStatus.SUCCESS
    payment.paid_at = datetime.utcnow()
    
    # Get registration
    registration = db.query(EventRegistration).filter(
        EventRegistration.payment_id == payment.id
    ).first()
    
    if registration:
        # UC005: Update registration status to CONFIRMED
        registration.registration_status = RegistrationStatus.CONFIRMED
        
        # UC005 A4: Generate WhatsApp link
        registration.whatsapp_link = generate_whatsapp_link(
            payment.event_id,
            current_user.id,
            registration.id
        )
        registration.confirmation_sent = True
        
        # Update event participant count
        event = db.query(Event).filter(Event.id == payment.event_id).first()
        if event:
            event.current_participants = event.current_participants + 1 + registration.num_copassengers
    
    db.commit()
    db.refresh(payment)
    
    return payment


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """UC005: Get payment details."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Verify ownership (or admin)
    if payment.user_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return payment


@router.post("/webhook/razorpay", status_code=status.HTTP_200_OK)
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    """
    UC005: Razorpay webhook endpoint for payment notifications.
    This is called by Razorpay after payment completion.
    """
    # Get webhook payload
    payload = await request.body()
    webhook_signature = request.headers.get("X-Razorpay-Signature")
    
    # Verify webhook signature
    # expected_signature = hmac.new(
    #     RAZORPAY_KEY_SECRET.encode(),
    #     payload,
    #     hashlib.sha256
    # ).hexdigest()
    # 
    # if expected_signature != webhook_signature:
    #     raise HTTPException(status_code=400, detail="Invalid webhook signature")
    
    # Parse payload and update payment
    # (Implementation depends on webhook event type)
    
    return {"status": "success"}


@router.post("/webhook/phonepe", status_code=status.HTTP_200_OK)
async def phonepe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    UC005: PhonePe webhook endpoint for payment notifications.
    """
    # Similar to Razorpay webhook logic
    return {"status": "success"}
