from datetime import datetime
import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
from app.database import get_db
from app.models.models import (
    ClubMembershipRequest,
    MembershipStatus,
    TBLRMembership,
    TharBengaluruMembership,
    User,
    UserRole,
    Vehicle,
)
from app.schemas.schemas import (
    ClubMembershipRequestCreate,
    ClubMembershipRequestResponse,
    ClubMembershipEligibilityResponse,
    ClubMembershipAutofillResponse,
    ClubMembershipPaymentResponse,
    ClubMembershipActivationResponse,
    TharBengaluruMembershipCreate,
    TharBengaluruMembershipResponse,
    TharBengaluruMembershipEligibilityResponse,
    TharBengaluruMembershipAutofillResponse,
    TharBengaluruMembershipPaymentResponse,
    TharBengaluruMembershipActivationResponse,
)
from app.routes.auth import get_current_user

router = APIRouter(prefix="/memberships/club-requests", tags=["membership"])
tb_router = APIRouter(prefix="/memberships/tb-requests", tags=["membership"])


def _membership_window_open() -> bool:
    """Toggle point for membership intake window."""
    return True


def _has_completed_workshop_trail(user_id: int, db: Session) -> bool:
    trail = db.query(TBLRMembership).filter(
        TBLRMembership.user_id == user_id,
        TBLRMembership.status == MembershipStatus.APPROVED
    ).order_by(TBLRMembership.updated_at.desc()).first()
    return trail is not None


def _get_existing_request(user_id: int, db: Session) -> Optional[ClubMembershipRequest]:
    return db.query(ClubMembershipRequest).filter(
        ClubMembershipRequest.user_id == user_id,
        ClubMembershipRequest.status.in_([MembershipStatus.PENDING, MembershipStatus.APPROVED])
    ).order_by(ClubMembershipRequest.created_at.desc()).first()


def _append_audit(entry_obj: ClubMembershipRequest, message: str) -> None:
    try:
        logs = json.loads(entry_obj.audit_log) if entry_obj.audit_log else []
    except Exception:
        logs = []
    logs.append({"at": datetime.utcnow().isoformat(), "message": message})
    entry_obj.audit_log = json.dumps(logs)


def _generate_membership_id(request_obj: ClubMembershipRequest, db: Session) -> str:
    sequence = db.query(ClubMembershipRequest).filter(ClubMembershipRequest.membership_id.isnot(None)).count() + 1
    year_yy = datetime.utcnow().strftime("%y")

    fuel = (request_obj.vehicle_fuel_type or "petrol").strip().lower()
    fuel_code = "D" if fuel == "diesel" else "P"

    model_text = (request_obj.vehicle_model or "").lower()
    variant_code = "R" if "roxx" in model_text else "T"

    transmission = (request_obj.vehicle_transmission_type or "manual").strip().lower()
    trans_code = "A" if "auto" in transmission else "M"

    reg_clean = "".join(ch for ch in (request_obj.vehicle_number or "") if ch.isalnum()).upper()
    reg_last4 = (reg_clean[-4:] if len(reg_clean) >= 4 else reg_clean.rjust(4, "0"))

    return f"TBC{sequence:04d}-{year_yy}{fuel_code}{variant_code}{trans_code}{reg_last4}"


def _get_or_404(request_id: int, db: Session) -> ClubMembershipRequest:
    obj = db.query(ClubMembershipRequest).filter(ClubMembershipRequest.id == request_id).first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    return obj


@router.get("/eligibility", response_model=ClubMembershipEligibilityResponse)
def check_membership_eligibility(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    reasons: List[str] = []

    window_open = _membership_window_open()
    if not window_open:
        reasons.append("Membership registration window is closed.")

    workshop_done = _has_completed_workshop_trail(current_user.id, db)
    if not workshop_done:
        reasons.append("You must complete the mandatory workshop trail before applying.")

    existing = _get_existing_request(current_user.id, db)
    has_pending = existing is not None and existing.status == MembershipStatus.PENDING
    has_active = existing is not None and existing.status == MembershipStatus.APPROVED and (existing.payment_status == "success")

    if has_pending:
        reasons.append("You already have a pending membership request.")
    if has_active:
        reasons.append("You already have an active club membership.")

    return ClubMembershipEligibilityResponse(
        eligible=len(reasons) == 0,
        reasons=reasons,
        workshop_trail_completed=workshop_done,
        membership_window_open=window_open,
        has_existing_membership=has_active,
        has_pending_request=has_pending,
    )


@router.get("/autofill", response_model=ClubMembershipAutofillResponse)
def get_autofill_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """UC005: Return partially auto-populated profile for membership form."""
    vehicle = db.query(Vehicle).filter(
        Vehicle.user_id == current_user.id
    ).order_by(Vehicle.is_primary.desc(), Vehicle.created_at.desc()).first()

    name_parts = (current_user.name or "").strip().split(" ", 1)
    first_name = name_parts[0] if name_parts else ""
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    return ClubMembershipAutofillResponse(
        tb_member_id=f"TBM{current_user.id:05d}",
        first_name=first_name,
        last_name=last_name,
        mobile_number=current_user.phone or "",
        email_address=current_user.email,
        residential_address=current_user.address,
        emergency_contact=current_user.emergency_contact,
        vehicle_make_model=(f"{vehicle.make} {vehicle.model}" if vehicle else None),
        vehicle_fuel_type=None,
        vehicle_transmission_type=None,
        vehicle_registration_number=vehicle.registration_number if vehicle else None,
        profile_photo_url=current_user.profile_photo,
        rc_document_url=None,
    )


@router.post("", response_model=ClubMembershipRequestResponse)
def submit_membership_request(
    request_data: ClubMembershipRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """UC005: Submit club membership request for existing THAR Bengaluru members."""
    eligibility = check_membership_eligibility(current_user=current_user, db=db)
    if not eligibility.eligible:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="; ".join(eligibility.reasons))

    if not request_data.terms_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Terms & Conditions must be accepted before submission."
        )

    # Ensure non-editable fields align with member profile identity.
    if request_data.email != current_user.email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email must match your registered profile.")
    if current_user.phone and request_data.phone != current_user.phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone must match your registered profile.")

    new_request = ClubMembershipRequest(
        user_id=current_user.id,
        name=request_data.name,
        email=request_data.email,
        phone=request_data.phone,
        vehicle_model=request_data.vehicle_model,
        vehicle_number=request_data.vehicle_number,
        registration_date=request_data.registration_date,
        reason=request_data.reason,
        residential_address=request_data.residential_address or current_user.address,
        emergency_contact=request_data.emergency_contact or current_user.emergency_contact,
        vehicle_fuel_type=request_data.vehicle_fuel_type,
        vehicle_transmission_type=request_data.vehicle_transmission_type,
        profile_photo_url=request_data.profile_photo_url or current_user.profile_photo,
        rc_document_url=request_data.rc_document_url,
        insurance_document_url=request_data.insurance_document_url,
        aadhaar_document_url=request_data.aadhaar_document_url,
        driving_license_document_url=request_data.driving_license_document_url,
        vehicle_modifications=request_data.vehicle_modifications,
        additional_info=request_data.additional_info,
        terms_accepted=request_data.terms_accepted,
        workshop_trail_completed=eligibility.workshop_trail_completed,
        payment_status="pending",
        payment_link_enabled=False,
        status=MembershipStatus.PENDING,
    )
    _append_audit(new_request, "Membership request submitted by user")

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
        requests = db.query(ClubMembershipRequest).offset(skip).limit(limit).all()
    else:
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
    """Get single membership request for current user/admin."""
    request_obj = _get_or_404(request_id, db)
    if current_user.role != UserRole.ADMIN and request_obj.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return request_obj


@router.delete("/{request_id}", status_code=status.HTTP_200_OK)
def delete_membership_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Allow user/admin to remove membership request for cleanup flows."""
    request_obj = _get_or_404(request_id, db)
    if current_user.role != UserRole.ADMIN and request_obj.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    if request_obj.status == MembershipStatus.APPROVED and request_obj.payment_status == "success":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Active memberships cannot be deleted")

    db.delete(request_obj)
    db.commit()
    return {"message": "Membership request deleted"}


@router.patch("/{request_id}/approve", response_model=ClubMembershipRequestResponse)
def approve_membership_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Approve a membership request (admin only) and unlock payment."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    request_obj = _get_or_404(request_id, db)
    if request_obj.status != MembershipStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve request with status: {request_obj.status.value}"
        )

    request_obj.status = MembershipStatus.APPROVED
    request_obj.payment_status = "pending"
    request_obj.payment_link_enabled = True
    request_obj.rejection_reason = None
    request_obj.approved_by_admin_id = current_user.id
    request_obj.reviewed_at = datetime.utcnow()
    _append_audit(request_obj, f"Approved by admin user_id={current_user.id}; payment unlocked")

    db.commit()
    db.refresh(request_obj)
    return request_obj


@router.patch("/{request_id}/reject", response_model=ClubMembershipRequestResponse)
def reject_membership_request(
    request_id: int,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reject a membership request (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    request_obj = _get_or_404(request_id, db)
    if request_obj.status != MembershipStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reject request with status: {request_obj.status.value}"
        )

    request_obj.status = MembershipStatus.REJECTED
    request_obj.payment_link_enabled = False
    request_obj.rejection_reason = reason
    request_obj.reviewed_at = datetime.utcnow()
    _append_audit(request_obj, f"Rejected by admin user_id={current_user.id}")

    db.commit()
    db.refresh(request_obj)
    return request_obj


@router.post("/{request_id}/payment/initiate", response_model=ClubMembershipPaymentResponse)
def initiate_membership_payment(
    request_id: int,
    payment_gateway: str = "razorpay",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """UC005: Initiate membership fee payment after admin approval."""
    request_obj = _get_or_404(request_id, db)
    if request_obj.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    if request_obj.status != MembershipStatus.APPROVED or not request_obj.payment_link_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment is not enabled for this request")

    if request_obj.payment_status == "success":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Membership payment already completed")

    request_obj.payment_gateway = payment_gateway
    request_obj.payment_order_id = f"mship_order_{request_obj.id}_{int(datetime.utcnow().timestamp())}"
    request_obj.payment_status = "pending"
    _append_audit(request_obj, f"Payment initiated via {payment_gateway}")

    payment_url = (
        f"https://payments.tharbengaluru.com/membership/pay?request_id={request_obj.id}"
        f"&order_id={request_obj.payment_order_id}&gateway={payment_gateway}"
    )

    db.commit()

    return ClubMembershipPaymentResponse(
        request_id=request_obj.id,
        payment_status=request_obj.payment_status,
        payment_gateway=request_obj.payment_gateway,
        payment_order_id=request_obj.payment_order_id,
        payment_url=payment_url,
        message="Payment initiated successfully"
    )


@router.post("/{request_id}/payment/success", response_model=ClubMembershipActivationResponse)
def confirm_membership_payment(
    request_id: int,
    gateway_payment_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """UC005: Confirm payment success and activate membership."""
    request_obj = _get_or_404(request_id, db)

    if current_user.role != UserRole.ADMIN and request_obj.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    if request_obj.status != MembershipStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request is not approved")

    request_obj.payment_status = "success"
    request_obj.payment_id = gateway_payment_id or f"mship_pay_{request_obj.id}_{int(datetime.utcnow().timestamp())}"

    if not request_obj.membership_id:
        request_obj.membership_id = _generate_membership_id(request_obj, db)

    request_obj.activated_at = datetime.utcnow()
    request_obj.whatsapp_group_name = "Thar Bengaluru Club - Official"

    # A5 path support: if link generation fails, keep activation with fallback message.
    try:
        request_obj.whatsapp_group_link = f"https://chat.whatsapp.com/invite/tbc{request_obj.id:04d}"
        request_obj.whatsapp_join_available = True
    except Exception:
        request_obj.whatsapp_group_link = None
        request_obj.whatsapp_join_available = False

    _append_audit(request_obj, "Membership activated after successful payment")

    db.commit()

    return ClubMembershipActivationResponse(
        request_id=request_obj.id,
        membership_id=request_obj.membership_id,
        membership_status="active",
        whatsapp_group_name=request_obj.whatsapp_group_name,
        whatsapp_group_link=request_obj.whatsapp_group_link,
        whatsapp_join_available=request_obj.whatsapp_join_available,
        message=(
            "Membership activated successfully"
            if request_obj.whatsapp_join_available
            else "Membership activated. Your WhatsApp link will be shared shortly."
        )
    )


@router.post("/{request_id}/payment/failure", response_model=ClubMembershipPaymentResponse)
def mark_membership_payment_failed(
    request_id: int,
    failure_reason: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """UC005 A4: Mark membership payment failure and keep request in payment-pending state."""
    request_obj = _get_or_404(request_id, db)
    if current_user.role != UserRole.ADMIN and request_obj.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    if request_obj.status != MembershipStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request is not approved")

    request_obj.payment_status = "failed"
    request_obj.payment_link_enabled = True
    if failure_reason:
        request_obj.additional_info = (request_obj.additional_info or "") + f"\nPayment Failure: {failure_reason}"

    _append_audit(request_obj, "Payment failure recorded; retry allowed")
    db.commit()

    return ClubMembershipPaymentResponse(
        request_id=request_obj.id,
        payment_status=request_obj.payment_status,
        payment_gateway=request_obj.payment_gateway,
        payment_order_id=request_obj.payment_order_id,
        payment_url=None,
        message="Payment failed. Membership remains approved and payment pending."
    )


@router.get("/{request_id}/activation", response_model=ClubMembershipActivationResponse)
def get_membership_activation_state(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """UC005: Get current activation state and WhatsApp onboarding details."""
    request_obj = _get_or_404(request_id, db)
    if current_user.role != UserRole.ADMIN and request_obj.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    membership_status = "active" if request_obj.status == MembershipStatus.APPROVED and request_obj.payment_status == "success" else request_obj.status.value
    message = "Membership activated" if membership_status == "active" else "Membership not activated yet"

    return ClubMembershipActivationResponse(
        request_id=request_obj.id,
        membership_id=request_obj.membership_id,
        membership_status=membership_status,
        whatsapp_group_name=request_obj.whatsapp_group_name,
        whatsapp_group_link=request_obj.whatsapp_group_link,
        whatsapp_join_available=bool(request_obj.whatsapp_join_available),
        message=message
    )


# ==================== UC006: REGULAR THAR BENGALURU MEMBERSHIP ====================

def _tb_get_or_404(request_id: int, db: Session) -> TharBengaluruMembership:
    obj = db.query(TharBengaluruMembership).filter(TharBengaluruMembership.id == request_id).first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TB membership request not found")
    return obj


def _append_tb_audit(entry_obj: TharBengaluruMembership, message: str) -> None:
    try:
        logs = json.loads(entry_obj.audit_log) if entry_obj.audit_log else []
    except Exception:
        logs = []
    logs.append({"at": datetime.utcnow().isoformat(), "message": message})
    entry_obj.audit_log = json.dumps(logs)


def _generate_tblr_membership_id(db: Session) -> str:
    sequence = db.query(TharBengaluruMembership).filter(
        TharBengaluruMembership.membership_id.isnot(None)
    ).count() + 1
    return f"TBLR{sequence:04d}"


def _validate_registration_format(value: str) -> bool:
    return re.match(r"^[A-Z]{2}-\d{2}-[A-Z]{2}-\d{4}$", value.strip().upper()) is not None


@tb_router.get("/eligibility", response_model=TharBengaluruMembershipEligibilityResponse)
def check_tb_membership_eligibility(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    reasons: List[str] = []

    workshop_done = _has_completed_workshop_trail(current_user.id, db)
    if not workshop_done:
        reasons.append("You must complete the mandatory workshop trail before applying.")

    existing = db.query(TharBengaluruMembership).filter(
        TharBengaluruMembership.user_id == current_user.id,
        TharBengaluruMembership.status == MembershipStatus.APPROVED,
        TharBengaluruMembership.payment_status == "success"
    ).order_by(TharBengaluruMembership.created_at.desc()).first()

    pending = db.query(TharBengaluruMembership).filter(
        TharBengaluruMembership.user_id == current_user.id,
        TharBengaluruMembership.status == MembershipStatus.PENDING
    ).order_by(TharBengaluruMembership.created_at.desc()).first()

    if existing:
        reasons.append("You are already an active Thar Bengaluru member.")
    if pending:
        reasons.append("You already have a pending membership request.")

    return TharBengaluruMembershipEligibilityResponse(
        eligible=len(reasons) == 0,
        reasons=reasons,
        workshop_trail_completed=workshop_done,
        has_existing_membership=existing is not None,
        has_pending_request=pending is not None,
    )


@tb_router.get("/autofill", response_model=TharBengaluruMembershipAutofillResponse)
def get_tb_autofill_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    vehicle = db.query(Vehicle).filter(
        Vehicle.user_id == current_user.id
    ).order_by(Vehicle.is_primary.desc(), Vehicle.created_at.desc()).first()

    parts = (current_user.name or "").strip().split(" ", 1)
    first_name = parts[0] if parts else None
    last_name = parts[1] if len(parts) > 1 else None

    vehicle_model = None
    if vehicle and vehicle.make and vehicle.make.lower() == "mahindra":
        if vehicle.model in ["Thar", "Thar Roxx"]:
            vehicle_model = vehicle.model

    return TharBengaluruMembershipAutofillResponse(
        first_name=first_name,
        last_name=last_name,
        mobile_number=current_user.phone,
        email_address=current_user.email,
        residential_address=current_user.address,
        emergency_contact=current_user.emergency_contact,
        vehicle_make="Mahindra",
        vehicle_model=vehicle_model,
        vehicle_registration_number=vehicle.registration_number if vehicle else None,
        profile_photo_url=current_user.profile_photo,
    )


@tb_router.post("", response_model=TharBengaluruMembershipResponse)
def submit_tb_membership_request(
    request_data: TharBengaluruMembershipCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    eligibility = check_tb_membership_eligibility(current_user=current_user, db=db)
    if not eligibility.eligible:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="; ".join(eligibility.reasons))

    if not request_data.terms_accepted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Terms & Conditions must be accepted.")

    if request_data.vehicle_make != "Mahindra":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vehicle make must be Mahindra.")

    if request_data.vehicle_model not in ["Thar", "Thar Roxx"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vehicle model must be Thar or Thar Roxx.")

    if request_data.vehicle_fuel_type not in ["Diesel", "Petrol", "Alternate"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid vehicle fuel type.")

    if request_data.vehicle_transmission_type not in ["Manual", "Automatic"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid vehicle transmission type.")

    if not _validate_registration_format(request_data.vehicle_registration_number):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vehicle registration format must be KA-03-NM-4040.")

    required_urls = [
        request_data.profile_photo_url,
        request_data.rc_document_url,
        request_data.aadhaar_document_url,
        request_data.driving_license_document_url,
    ]
    if any(not u for u in required_urls):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Profile photo, RC, Aadhaar, and Driving License are mandatory.")

    if request_data.email_address != current_user.email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email must match registered profile.")

    new_request = TharBengaluruMembership(
        user_id=current_user.id,
        first_name=request_data.first_name,
        last_name=request_data.last_name,
        mobile_number=request_data.mobile_number,
        email_address=request_data.email_address,
        residential_address=request_data.residential_address,
        emergency_contact=request_data.emergency_contact,
        vehicle_make="Mahindra",
        vehicle_model=request_data.vehicle_model,
        vehicle_fuel_type=request_data.vehicle_fuel_type,
        vehicle_transmission_type=request_data.vehicle_transmission_type,
        vehicle_registration_number=request_data.vehicle_registration_number.strip().upper(),
        vehicle_modifications=request_data.vehicle_modifications,
        profile_photo_url=request_data.profile_photo_url,
        rc_document_url=request_data.rc_document_url,
        insurance_document_url=request_data.insurance_document_url,
        aadhaar_document_url=request_data.aadhaar_document_url,
        driving_license_document_url=request_data.driving_license_document_url,
        additional_info=request_data.additional_info,
        terms_accepted=True,
        status=MembershipStatus.PENDING,
        payment_status="pending",
        payment_link_enabled=False,
    )
    _append_tb_audit(new_request, "TB membership request submitted by user")

    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    return new_request


@tb_router.get("", response_model=List[TharBengaluruMembershipResponse])
def list_tb_membership_requests(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == UserRole.ADMIN:
        return db.query(TharBengaluruMembership).offset(skip).limit(limit).all()
    return db.query(TharBengaluruMembership).filter(
        TharBengaluruMembership.user_id == current_user.id
    ).offset(skip).limit(limit).all()


@tb_router.get("/{request_id}", response_model=TharBengaluruMembershipResponse)
def get_tb_membership_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    request_obj = _tb_get_or_404(request_id, db)
    if current_user.role != UserRole.ADMIN and request_obj.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return request_obj


@tb_router.delete("/{request_id}", status_code=status.HTTP_200_OK)
def delete_tb_membership_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    request_obj = _tb_get_or_404(request_id, db)
    if current_user.role != UserRole.ADMIN and request_obj.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    if request_obj.status == MembershipStatus.APPROVED and request_obj.payment_status == "success":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Active memberships cannot be deleted")

    db.delete(request_obj)
    db.commit()
    return {"message": "TB membership request deleted"}


@tb_router.patch("/{request_id}/approve", response_model=TharBengaluruMembershipResponse)
def approve_tb_membership_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    request_obj = _tb_get_or_404(request_id, db)
    if request_obj.status != MembershipStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending requests can be approved")

    request_obj.status = MembershipStatus.APPROVED
    request_obj.payment_status = "pending"
    request_obj.payment_link_enabled = True
    request_obj.rejection_reason = None
    request_obj.approved_by_admin_id = current_user.id
    request_obj.reviewed_at = datetime.utcnow()
    _append_tb_audit(request_obj, f"Approved by admin user_id={current_user.id}; payment unlocked")

    db.commit()
    db.refresh(request_obj)
    return request_obj


@tb_router.patch("/{request_id}/reject", response_model=TharBengaluruMembershipResponse)
def reject_tb_membership_request(
    request_id: int,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    request_obj = _tb_get_or_404(request_id, db)
    if request_obj.status != MembershipStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending requests can be rejected")

    request_obj.status = MembershipStatus.REJECTED
    request_obj.payment_link_enabled = False
    request_obj.rejection_reason = reason
    request_obj.approved_by_admin_id = current_user.id
    request_obj.reviewed_at = datetime.utcnow()
    _append_tb_audit(request_obj, f"Rejected by admin user_id={current_user.id}")

    db.commit()
    db.refresh(request_obj)
    return request_obj


@tb_router.patch("/{request_id}/request-more-info", response_model=TharBengaluruMembershipResponse)
def request_more_info_tb_membership_request(
    request_id: int,
    note: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    request_obj = _tb_get_or_404(request_id, db)
    if request_obj.status != MembershipStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending requests can be reviewed")

    request_obj.additional_info = (request_obj.additional_info or "") + f"\nAdmin Note: {note}"
    request_obj.reviewed_at = datetime.utcnow()
    _append_tb_audit(request_obj, f"Request more information by admin user_id={current_user.id}")

    db.commit()
    db.refresh(request_obj)
    return request_obj


@tb_router.post("/{request_id}/payment/initiate", response_model=TharBengaluruMembershipPaymentResponse)
def initiate_tb_membership_payment(
    request_id: int,
    payment_gateway: str = "razorpay",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    request_obj = _tb_get_or_404(request_id, db)
    if request_obj.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    if request_obj.status != MembershipStatus.APPROVED or not request_obj.payment_link_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment is not enabled for this request")

    if request_obj.payment_status == "success":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Membership payment already completed")

    request_obj.payment_gateway = payment_gateway
    request_obj.payment_order_id = f"tb_order_{request_obj.id}_{int(datetime.utcnow().timestamp())}"
    request_obj.payment_status = "pending"
    _append_tb_audit(request_obj, f"Payment initiated via {payment_gateway}")

    payment_url = (
        f"https://payments.tharbengaluru.com/tb-membership/pay?request_id={request_obj.id}"
        f"&order_id={request_obj.payment_order_id}&gateway={payment_gateway}"
    )

    db.commit()

    return TharBengaluruMembershipPaymentResponse(
        request_id=request_obj.id,
        payment_status=request_obj.payment_status,
        payment_gateway=request_obj.payment_gateway,
        payment_order_id=request_obj.payment_order_id,
        payment_url=payment_url,
        message="Payment initiated successfully"
    )


@tb_router.post("/{request_id}/payment/success", response_model=TharBengaluruMembershipActivationResponse)
def confirm_tb_membership_payment(
    request_id: int,
    gateway_payment_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    request_obj = _tb_get_or_404(request_id, db)
    if current_user.role != UserRole.ADMIN and request_obj.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    if request_obj.status != MembershipStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request is not approved")

    request_obj.payment_status = "success"
    request_obj.payment_id = gateway_payment_id or f"tb_pay_{request_obj.id}_{int(datetime.utcnow().timestamp())}"
    request_obj.membership_id = request_obj.membership_id or _generate_tblr_membership_id(db)
    request_obj.activated_at = datetime.utcnow()
    request_obj.whatsapp_group_name = "Thar Bengaluru - Official"
    request_obj.whatsapp_group_link = f"https://chat.whatsapp.com/invite/tblr{request_obj.id:04d}"
    request_obj.whatsapp_join_available = True
    _append_tb_audit(request_obj, "TB membership activated after successful payment")

    db.commit()

    return TharBengaluruMembershipActivationResponse(
        request_id=request_obj.id,
        membership_id=request_obj.membership_id,
        membership_status="active",
        whatsapp_group_name=request_obj.whatsapp_group_name,
        whatsapp_group_link=request_obj.whatsapp_group_link,
        whatsapp_join_available=request_obj.whatsapp_join_available,
        message="Membership activated successfully"
    )


@tb_router.post("/{request_id}/payment/failure", response_model=TharBengaluruMembershipPaymentResponse)
def mark_tb_membership_payment_failed(
    request_id: int,
    failure_reason: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    request_obj = _tb_get_or_404(request_id, db)
    if current_user.role != UserRole.ADMIN and request_obj.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    if request_obj.status != MembershipStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request is not approved")

    request_obj.payment_status = "failed"
    request_obj.payment_link_enabled = True
    if failure_reason:
        request_obj.additional_info = (request_obj.additional_info or "") + f"\nPayment Failure: {failure_reason}"
    _append_tb_audit(request_obj, "Payment failure recorded; retry allowed")
    db.commit()

    return TharBengaluruMembershipPaymentResponse(
        request_id=request_obj.id,
        payment_status=request_obj.payment_status,
        payment_gateway=request_obj.payment_gateway,
        payment_order_id=request_obj.payment_order_id,
        payment_url=None,
        message="Payment failed. Membership remains approved and payment pending."
    )


@tb_router.get("/{request_id}/activation", response_model=TharBengaluruMembershipActivationResponse)
def get_tb_membership_activation_state(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    request_obj = _tb_get_or_404(request_id, db)
    if current_user.role != UserRole.ADMIN and request_obj.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    membership_status = "active" if request_obj.status == MembershipStatus.APPROVED and request_obj.payment_status == "success" else request_obj.status.value
    message = "Membership activated" if membership_status == "active" else "Membership not activated yet"

    return TharBengaluruMembershipActivationResponse(
        request_id=request_obj.id,
        membership_id=request_obj.membership_id,
        membership_status=membership_status,
        whatsapp_group_name=request_obj.whatsapp_group_name,
        whatsapp_group_link=request_obj.whatsapp_group_link,
        whatsapp_join_available=bool(request_obj.whatsapp_join_available),
        message=message,
    )
