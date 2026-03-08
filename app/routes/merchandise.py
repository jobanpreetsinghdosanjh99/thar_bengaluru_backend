from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models.models import (
    Merchandise, Vendor, MerchandiseOrder, MerchandiseOrderItem, User, PaymentStatus, OrderStatus
)
from app.schemas.schemas import (
    MerchandiseCreate, MerchandiseResponse, MerchandiseDetailResponse,
    MerchandiseCheckout, MerchandiseOrderResponse, MerchandiseOrderPaymentRedirect,
    MerchandiseOrderItemResponse
)
from app.routes.auth import get_current_user, get_optional_current_user
from app.utils import (
    generate_order_number, prepare_order_summary,
    notify_vendor_complete, process_payment_success, process_payment_failure
)

router = APIRouter(prefix="/merchandise", tags=["merchandise"])


# ==================== UC004E: MERCHANDISE CATEGORIES ====================

@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    """UC004E: Get all merchandise categories with counts."""
    categories = {
        "Apparel": "👕",
        "Hoodies": "🧥",
        "Caps": "🧢",
        "Stickers": "🎨",
        "Accessories": "🎒",
        "Keychains": "🔑",
        "Mugs": "☕",
    }
    return categories


# ==================== UC004E: BROWSE MERCHANDISE ====================

@router.get("", response_model=List[MerchandiseResponse])
def list_merchandise(
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """UC004E: Get list of merchandise, optionally filtered by category."""
    query = db.query(Merchandise).filter(Merchandise.stock > 0)
    
    if category:
        query = query.filter(Merchandise.category == category)
    
    # Order by featured first, then by rating
    merchandise_list = query.order_by(
        Merchandise.is_featured.desc(), 
        Merchandise.rating.desc()
    ).offset(skip).limit(limit).all()
    
    # Convert to response format with vendor serialization
    result = []
    for merch in merchandise_list:
        merch_data = {
            "id": merch.id,
            "vendor_id": merch.vendor_id,
            "name": merch.name,
            "description": merch.description,
            "long_description": merch.long_description,
            "category": merch.category,
            "price": merch.price,
            "image_url": merch.image_url,
            "images": merch.images,
            "sizes": merch.sizes,
            "colors": merch.colors,
            "stock": merch.stock,
            "features": merch.features,
            "material": merch.material,
            "brand": merch.brand,
            "rating": merch.rating,
            "reviews": merch.reviews,
            "is_featured": merch.is_featured,
            "is_on_sale": merch.is_on_sale,
            "discounted_price": merch.discounted_price,
            "created_at": merch.created_at,
            "updated_at": merch.updated_at,
            "vendor": {
                "id": merch.vendor.id,
                "name": merch.vendor.name,
                "email": merch.vendor.email,
                "whatsapp_number": merch.vendor.whatsapp_number
            } if merch.vendor else None
        }
        result.append(merch_data)
    
    return result


# ==================== UC004E: ORDER HISTORY (must come before /{merchandise_id}) ====================

@router.get("/orders", response_model=List[MerchandiseOrderResponse])
def get_user_merchandise_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """UC004E: Get all merchandise orders for the logged-in user."""
    orders = db.query(MerchandiseOrder).filter(
        MerchandiseOrder.user_id == current_user.id
    ).order_by(MerchandiseOrder.created_at.desc()).all()
    
    # Convert to response format
    result = []
    for order in orders:
        order_data = {
            "id": order.id,
            "order_number": order.order_number,
            "customer_name": order.customer_name,
            "customer_email": order.customer_email,
            "customer_phone": order.customer_phone,
            "shipping_address": order.shipping_address,
            "total_amount": order.total_amount,
            "currency": order.currency,
            "payment_gateway": order.payment_gateway,
            "payment_status": order.payment_status.value,
            "order_status": order.order_status.value,
            "vendor_notification_sent": order.vendor_notification_sent,
            "user_confirmation_sent": order.user_confirmation_sent,
            "notes": order.notes,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "items": [],
            "vendor": {
                "id": order.vendor.id,
                "name": order.vendor.name,
                "email": order.vendor.email,
                "whatsapp_number": order.vendor.whatsapp_number
            } if order.vendor else None
        }
        
        # Add order items with merchandise details
        for item in order.items:
            item_data = {
                "id": item.id,
                "merchandise_id": item.merchandise_id,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
                "selected_size": item.selected_size,
                "selected_color": item.selected_color,
                "merchandise": {
                    "id": item.merchandise.id,
                    "vendor_id": item.merchandise.vendor_id,
                    "name": item.merchandise.name,
                    "description": item.merchandise.description,
                    "long_description": item.merchandise.long_description,
                    "category": item.merchandise.category,
                    "price": item.merchandise.price,
                    "image_url": item.merchandise.image_url,
                    "images": item.merchandise.images,
                    "sizes": item.merchandise.sizes,
                    "colors": item.merchandise.colors,
                    "stock": item.merchandise.stock,
                    "features": item.merchandise.features,
                    "material": item.merchandise.material,
                    "brand": item.merchandise.brand,
                    "rating": item.merchandise.rating,
                    "reviews": item.merchandise.reviews,
                    "is_featured": item.merchandise.is_featured,
                    "is_on_sale": item.merchandise.is_on_sale,
                    "discounted_price": item.merchandise.discounted_price,
                    "created_at": item.merchandise.created_at,
                    "updated_at": item.merchandise.updated_at,
                    "vendor": None
                } if item.merchandise else None
            }
            order_data["items"].append(item_data)
        
        result.append(order_data)
    
    return result


@router.get("/orders/{order_id}", response_model=MerchandiseOrderResponse)
def get_merchandise_order_details(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """UC004E: Get specific merchandise order details."""
    order = db.query(MerchandiseOrder).filter(
        MerchandiseOrder.id == order_id,
        MerchandiseOrder.user_id == current_user.id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Format response
    result = {
        "id": order.id,
        "order_number": order.order_number,
        "customer_name": order.customer_name,
        "customer_email": order.customer_email,
        "customer_phone": order.customer_phone,
        "shipping_address": order.shipping_address,
        "total_amount": order.total_amount,
        "currency": order.currency,
        "payment_gateway": order.payment_gateway,
        "payment_status": order.payment_status.value,
        "order_status": order.order_status.value,
        "vendor_notification_sent": order.vendor_notification_sent,
        "user_confirmation_sent": order.user_confirmation_sent,
        "notes": order.notes,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "items": [],
        "vendor": {
            "id": order.vendor.id,
            "name": order.vendor.name,
            "email": order.vendor.email,
            "whatsapp_number": order.vendor.whatsapp_number
        } if order.vendor else None
    }
    
    # Add order items
    for item in order.items:
        item_data = {
            "id": item.id,
            "merchandise_id": item.merchandise_id,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "total_price": item.total_price,
            "selected_size": item.selected_size,
            "selected_color": item.selected_color,
            "merchandise": {
                "id": item.merchandise.id,
                "name": item.merchandise.name,
                "description": item.merchandise.description,
                "long_description": item.merchandise.long_description,
                "image_url": item.merchandise.image_url,
                "category": item.merchandise.category,
                "brand": item.merchandise.brand
            } if item.merchandise else None
        }
        result["items"].append(item_data)
    
    return result


# ==================== UC004E: ORDER HISTORY (must come before /{merchandise_id}) ====================

# ==================== UC004E: ORDER HISTORY ====================

@router.get("/orders", response_model=List[MerchandiseOrderResponse])
def get_user_merchandise_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """UC004E: Get all merchandise orders for the logged-in user."""
    orders = db.query(MerchandiseOrder).filter(
        MerchandiseOrder.user_id == current_user.id
    ).order_by(MerchandiseOrder.created_at.desc()).all()
    
    # Convert to response format
    result = []
    for order in orders:
        order_data = {
            "id": order.id,
            "order_number": order.order_number,
            "customer_name": order.customer_name,
            "customer_email": order.customer_email,
            "customer_phone": order.customer_phone,
            "shipping_address": order.shipping_address,
            "total_amount": order.total_amount,
            "currency": order.currency,
            "payment_gateway": order.payment_gateway,
            "payment_status": order.payment_status.value,
            "order_status": order.order_status.value,
            "vendor_notification_sent": order.vendor_notification_sent,
            "user_confirmation_sent": order.user_confirmation_sent,
            "notes": order.notes,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "items": [],
            "vendor": {
                "id": order.vendor.id,
                "name": order.vendor.name,
                "email": order.vendor.email,
                "whatsapp_number": order.vendor.whatsapp_number
            } if order.vendor else None
        }
        
        # Add order items with merchandise details
        for item in order.items:
            item_data = {
                "id": item.id,
                "merchandise_id": item.merchandise_id,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
                "selected_size": item.selected_size,
                "selected_color": item.selected_color,
                "merchandise": {
                    "id": item.merchandise.id,
                    "name": item.merchandise.name,
                    "description": item.merchandise.description,
                    "image_url": item.merchandise.image_url,
                    "category": item.merchandise.category
                } if item.merchandise else None
            }
            order_data["items"].append(item_data)
        
        result.append(order_data)
    
    return result


@router.get("/orders/{order_id}", response_model=MerchandiseOrderResponse)
def get_merchandise_order_details(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """UC004E: Get specific merchandise order details."""
    order = db.query(MerchandiseOrder).filter(
        MerchandiseOrder.id == order_id,
        MerchandiseOrder.user_id == current_user.id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Format response
    result = {
        "id": order.id,
        "order_number": order.order_number,
        "customer_name": order.customer_name,
        "customer_email": order.customer_email,
        "customer_phone": order.customer_phone,
        "shipping_address": order.shipping_address,
        "total_amount": order.total_amount,
        "currency": order.currency,
        "payment_gateway": order.payment_gateway,
        "payment_status": order.payment_status.value,
        "order_status": order.order_status.value,
        "vendor_notification_sent": order.vendor_notification_sent,
        "user_confirmation_sent": order.user_confirmation_sent,
        "notes": order.notes,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "items": [],
        "vendor": {
            "id": order.vendor.id,
            "name": order.vendor.name,
            "email": order.vendor.email,
            "whatsapp_number": order.vendor.whatsapp_number
        } if order.vendor else None
    }
    
    # Add order items
    for item in order.items:
        item_data = {
            "id": item.id,
            "merchandise_id": item.merchandise_id,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "total_price": item.total_price,
            "selected_size": item.selected_size,
            "selected_color": item.selected_color,
            "merchandise": {
                "id": item.merchandise.id,
                "name": item.merchandise.name,
                "description": item.merchandise.description,
                "long_description": item.merchandise.long_description,
                "image_url": item.merchandise.image_url,
                "category": item.merchandise.category,
                "brand": item.merchandise.brand
            } if item.merchandise else None
        }
        result["items"].append(item_data)
    
    return result


@router.get("/{merchandise_id}", response_model=MerchandiseDetailResponse)
def get_merchandise(merchandise_id: int, db: Session = Depends(get_db)):
    """UC004E: Get single merchandise details with vendor information."""
    merchandise = db.query(Merchandise).filter(Merchandise.id == merchandise_id).first()
    if not merchandise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchandise not found"
        )
    
    # Convert to dict and add vendor info
    result = {
        "id": merchandise.id,
        "vendor_id": merchandise.vendor_id,
        "name": merchandise.name,
        "description": merchandise.description,
        "long_description": merchandise.long_description,
        "category": merchandise.category,
        "price": merchandise.price,
        "image_url": merchandise.image_url,
        "images": merchandise.images,
        "sizes": merchandise.sizes,
        "colors": merchandise.colors,
        "stock": merchandise.stock,
        "features": merchandise.features,
        "material": merchandise.material,
        "brand": merchandise.brand,
        "rating": merchandise.rating,
        "reviews": merchandise.reviews,
        "is_featured": merchandise.is_featured,
        "is_on_sale": merchandise.is_on_sale,
        "discounted_price": merchandise.discounted_price,
        "created_at": merchandise.created_at,
        "updated_at": merchandise.updated_at,
        "vendor": {
            "id": merchandise.vendor.id,
            "name": merchandise.vendor.name,
            "email": merchandise.vendor.email,
            "whatsapp_number": merchandise.vendor.whatsapp_number
        } if merchandise.vendor else None
    }
    
    return result


# ==================== UC004E: ADMIN - CREATE MERCHANDISE ====================

@router.post("", response_model=MerchandiseResponse)
def create_merchandise(
    merch_data: MerchandiseCreate, 
    db: Session = Depends(get_db)
):
    """UC004E: Create a new merchandise item (admin only in production)."""
    # Verify vendor exists
    vendor = db.query(Vendor).filter(Vendor.id == merch_data.vendor_id).first()
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    new_merchandise = Merchandise(
        vendor_id=merch_data.vendor_id,
        name=merch_data.name,
        description=merch_data.description,
        long_description=merch_data.long_description,
        category=merch_data.category,
        price=merch_data.price,
        image_url=merch_data.image_url,
        images=merch_data.images,
        sizes=merch_data.sizes,
        colors=merch_data.colors,
        stock=merch_data.stock,
        features=merch_data.features,
        material=merch_data.material,
        brand=merch_data.brand,
        rating=merch_data.rating or 0.0,
        reviews=merch_data.reviews or 0,
        is_featured=merch_data.is_featured or False,
        is_on_sale=merch_data.is_on_sale or False,
        discounted_price=merch_data.discounted_price
    )
    db.add(new_merchandise)
    db.commit()
    db.refresh(new_merchandise)
    return new_merchandise


# ==================== UC004E: CHECKOUT & ORDERING ====================

def _validate_merchandise_stock(items_data: List, db: Session) -> List[tuple]:
    """Validate stock availability for merchandise cart items. Returns list of (Merchandise, quantity, size, color) tuples."""
    item_list = []
    for item_data in items_data:
        # Accept either dict payloads or Pydantic objects
        merchandise_id = item_data.get("merchandise_id") if isinstance(item_data, dict) else getattr(item_data, "merchandise_id", None)
        quantity = item_data.get("quantity") if isinstance(item_data, dict) else getattr(item_data, "quantity", None)
        size = item_data.get("size") if isinstance(item_data, dict) else getattr(item_data, "size", None)
        color = item_data.get("color") if isinstance(item_data, dict) else getattr(item_data, "color", None)

        if merchandise_id is None or quantity is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid cart item payload"
            )

        merchandise = db.query(Merchandise).filter(Merchandise.id == merchandise_id).first()
        if not merchandise or merchandise.stock < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Merchandise '{merchandise.name if merchandise else merchandise_id}' is no longer available or insufficient stock."
            )
        item_list.append((merchandise, quantity, size, color))
    return item_list


@router.post("/checkout", response_model=MerchandiseOrderPaymentRedirect)
def checkout_merchandise(
    checkout_data: MerchandiseCheckout,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    UC004E: Checkout merchandise. Creates order and redirects to vendor's payment gateway.
    Supports both logged-in users and guest checkout.
    """
    try:
        # Validate stock before proceeding
        items_with_stock = _validate_merchandise_stock(checkout_data.items, db)
        
        if not items_with_stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cart is empty"
            )
        
        # Get vendor from first item (all items must be from same vendor)
        first_vendor = items_with_stock[0][0].vendor
        
        # Verify all items are from same vendor
        for merchandise, _, _, _ in items_with_stock:
            if merchandise.vendor_id != first_vendor.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="All items must be from the same vendor"
                )
        
        # Calculate total amount (use discounted price if on sale)
        total_amount = 0.0
        for merchandise, quantity, _, _ in items_with_stock:
            price = merchandise.discounted_price if merchandise.is_on_sale and merchandise.discounted_price else merchandise.price
            total_amount += price * quantity
        
        # Create order
        order_number = generate_order_number("MERCH")
        order = MerchandiseOrder(
            user_id=current_user.id if current_user else None,
            vendor_id=first_vendor.id,
            order_number=order_number,
            customer_name=checkout_data.customer_name,
            customer_email=checkout_data.customer_email,
            customer_phone=checkout_data.customer_phone,
            shipping_address=checkout_data.shipping_address,
            total_amount=total_amount,
            currency="INR",
            payment_gateway=first_vendor.payment_gateway,
            order_status=OrderStatus.PENDING,
            notes=checkout_data.notes
        )
        
        db.add(order)
        db.flush()
        
        # Add order items
        for merchandise, quantity, size, color in items_with_stock:
            price = merchandise.discounted_price if merchandise.is_on_sale and merchandise.discounted_price else merchandise.price
            order_item = MerchandiseOrderItem(
                order_id=order.id,
                merchandise_id=merchandise.id,
                quantity=quantity,
                unit_price=price,
                total_price=price * quantity,
                selected_size=size,
                selected_color=color
            )
            db.add(order_item)
        
        db.commit()
        db.refresh(order)
        
        # Generate payment gateway redirect URL
        # In production, integrate with actual vendor payment gateway API
        gateway_redirect_url = f"{first_vendor.payment_gateway_url}?order_id={order.id}&amount={total_amount}&email={checkout_data.customer_email}"
        
        return MerchandiseOrderPaymentRedirect(
            order_id=order.id,
            order_number=order_number,
            payment_url=gateway_redirect_url,
            payment_gateway=first_vendor.payment_gateway,
            gateway_order_id=None,
            amount=total_amount,
            currency="INR"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Checkout failed: {str(e)}"
        )


# ==================== UC004E: PAYMENT WEBHOOKS ====================

@router.post("/payment/success/{order_id}")
def merchandise_payment_success(order_id: int, db: Session = Depends(get_db)):
    """
    UC004E: Payment success webhook. Called by vendor payment gateway.
    Updates order status, inventory, and sends notifications.
    """
    try:
        order = db.query(MerchandiseOrder).filter(MerchandiseOrder.id == order_id).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        
        if order.payment_status == PaymentStatus.SUCCESS:
            return {"message": "Order already processed"}
        
        # Process payment success using utility
        result = process_payment_success(order, db)
        
        # Send vendor notifications
        notify_vendor_complete(order.vendor, prepare_order_summary(order), "Merchandise")
        
        # Mark notifications as sent
        order.vendor_notification_sent = True
        order.order_status = OrderStatus.VENDOR_NOTIFIED
        db.commit()
        
        return {
            "message": result["message"],
            "order_number": order.order_number,
            "order_id": order.id
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment success processing failed: {str(e)}"
        )


@router.post("/payment/failure/{order_id}")
def merchandise_payment_failure(order_id: int, db: Session = Depends(get_db)):
    """
    UC004E: Payment failure webhook. Called when vendor payment gateway rejects payment.
    """
    try:
        order = db.query(MerchandiseOrder).filter(MerchandiseOrder.id == order_id).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        
        # Process payment failure using utility
        result = process_payment_failure(order, db, failure_reason="Payment rejected by gateway")
        
        return {
            "message": result["message"],
            "order_number": order.order_number
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment failure processing failed: {str(e)}"
        )

