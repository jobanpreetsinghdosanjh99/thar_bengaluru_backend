from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import requests
import json
from app.database import get_db
from app.models.models import (
    Accessory, Vendor, AccessoryOrder, AccessoryOrderItem, CartItem, User, PaymentStatus, OrderStatus
)
from app.schemas.schemas import (
    AccessoryDetailResponse, AccessoryCheckout, AccessoryOrderResponse, 
    AccessoryOrderPaymentRedirect, VendorResponse
)
from app.routes.auth import get_current_user, get_optional_current_user

router = APIRouter(prefix="/accessories", tags=["accessories"])


# ==================== UC004D: ACCESSORY CATEGORIES ====================

@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    """Get all accessory categories with counts."""
    categories = {
        "Recovery Gear": "🔗",
        "Lighting": "💡",
        "Suspension": "🛞",
        "Tires & Wheels": "🛞",
        "Protection": "🛡️",
        "Storage": "📦",
        "Cooling": "❄️",
        "Winch & Recovery": "🔗",
    }
    return categories


# ==================== UC004D: BROWSE ACCESSORIES ====================

@router.get("", response_model=List[AccessoryDetailResponse])
def list_accessories(
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get list of accessories, optionally filtered by category."""
    query = db.query(Accessory).filter(Accessory.stock > 0)
    
    if category:
        query = query.filter(Accessory.category == category)
    
    accessories = query.order_by(Accessory.is_featured.desc(), Accessory.rating.desc()).offset(skip).limit(limit).all()
    return accessories


# ==================== UC004D: CHECKOUT & ORDERING ====================

def _generate_order_number(db: Session) -> str:
    """Generate unique order number in format ORD-YYYYMMDD-XXXX."""
    from datetime import datetime
    date_str = datetime.utcnow().strftime("%Y%m%d")
    # Get count of orders today
    today = datetime.utcnow().date()
    count = db.query(AccessoryOrder).filter(
        AccessoryOrder.created_at >= datetime.combine(today, datetime.min.time())
    ).count()
    return f"ORD-{date_str}-{count + 1:04d}"


def _validate_stock(items_data: List, db: Session) -> List[tuple]:
    """Validate stock availability for cart items. Returns list of (Accessory, quantity) tuples."""
    item_list = []
    for item_data in items_data:
        # Accept either dict payloads or Pydantic objects.
        product_id = item_data.get("product_id") if isinstance(item_data, dict) else getattr(item_data, "product_id", None)
        quantity = item_data.get("quantity") if isinstance(item_data, dict) else getattr(item_data, "quantity", None)

        if product_id is None or quantity is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid cart item payload"
            )

        accessory = db.query(Accessory).filter(Accessory.id == product_id).first()
        if not accessory or accessory.stock < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"One or more items are no longer available or insufficient stock."
            )
        item_list.append((accessory, quantity))
    return item_list


@router.post("/checkout", response_model=AccessoryOrderPaymentRedirect)
def checkout_accessories(
    checkout_data: AccessoryCheckout,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    UC004D: Checkout accessories. Creates order and redirects to vendor's payment gateway.
    Supports both logged-in users and guest checkout.
    """
    try:
        # Validate stock before proceeding
        items_with_stock = _validate_stock(checkout_data.items, db)
        
        if not items_with_stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cart is empty"
            )
        
        # Get vendor from first item (all items must be from same vendor)
        first_vendor = items_with_stock[0][0].vendor
        
        # Verify all items are from same vendor
        for accessory, _ in items_with_stock:
            if accessory.vendor_id != first_vendor.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="All items must be from the same vendor"
                )
        
        # Calculate total amount
        total_amount = sum(accessory.price * quantity for accessory, quantity in items_with_stock)
        
        # Create order
        order_number = _generate_order_number(db)
        order = AccessoryOrder(
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
            order_status=OrderStatus.PENDING
        )
        
        db.add(order)
        db.flush()
        
        # Add order items
        for accessory, quantity in items_with_stock:
            order_item = AccessoryOrderItem(
                order_id=order.id,
                accessory_id=accessory.id,
                quantity=quantity,
                unit_price=accessory.price,
                total_price=accessory.price * quantity
            )
            db.add(order_item)
        
        db.commit()
        db.refresh(order)
        
        # Generate payment gateway redirect URL
        # For this example, we'll use a placeholder. In production, use actual vendor API.
        gateway_redirect_url = f"{first_vendor.payment_gateway_url}?order_id={order.id}&amount={total_amount}&email={checkout_data.customer_email}"
        
        return AccessoryOrderPaymentRedirect(
            order_id=order.id,
            order_number=order_number,
            gateway_redirect_url=gateway_redirect_url,
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


# ==================== UC004D: PAYMENT WEBHOOKS ====================

@router.post("/payment/success/{order_id}")
def payment_success(order_id: int, db: Session = Depends(get_db)):
    """
    UC004D: Payment success webhook. Called by vendor payment gateway.
    Updates order status, inventory, and sends notifications.
    """
    try:
        order = db.query(AccessoryOrder).filter(AccessoryOrder.id == order_id).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        
        if order.payment_status == PaymentStatus.SUCCESS:
            return {"message": "Order already processed"}
        
        # Update payment status
        order.payment_status = PaymentStatus.SUCCESS
        order.order_status = OrderStatus.PAYMENT_SUCCESS
        
        # Update inventory (deduct stock)
        for order_item in order.items:
            order_item.accessory.stock -= order_item.quantity
        
        db.commit()
        
        # Send vendor notifications (email + WhatsApp)
        _send_vendor_notifications(order, db)
        
        # Mark notifications as sent
        order.vendor_notification_sent = True
        order.order_status = OrderStatus.VENDOR_NOTIFIED
        db.commit()
        
        return {
            "message": "Payment successful and order confirmed",
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
def payment_failure(order_id: int, db: Session = Depends(get_db)):
    """
    UC004D: Payment failure webhook. Called when vendor payment gateway rejects payment.
    """
    try:
        order = db.query(AccessoryOrder).filter(AccessoryOrder.id == order_id).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        
        order.payment_status = PaymentStatus.FAILED
        order.order_status = OrderStatus.PAYMENT_FAILED
        
        db.commit()
        
        return {
            "message": "Payment unsuccessful. No charges were made.",
            "order_number": order.order_number
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment failure processing failed: {str(e)}"
        )


# ==================== UC004D: VENDOR NOTIFICATIONS ====================

def _send_vendor_notifications(order: AccessoryOrder, db: Session) -> None:
    """
    UC004D: Send order details to vendor via Email and WhatsApp.
    """
    vendor = order.vendor
    
    # Prepare order summary
    order_summary = _prepare_order_summary(order)
    
    # Send Email notification
    try:
        _send_email_notification(vendor, order, order_summary)
        order.vendor_notification_email_sent = True
    except Exception as e:
        print(f"Email notification failed for vendor {vendor.id}: {str(e)}")
    
    # Send WhatsApp notification
    try:
        _send_whatsapp_notification(vendor, order, order_summary)
        order.vendor_notification_whatsapp_sent = True
    except Exception as e:
        print(f"WhatsApp notification failed for vendor {vendor.id}: {str(e)}")


def _prepare_order_summary(order: AccessoryOrder) -> dict:
    """Prepare order summary for notifications."""
    items_list = []
    for item in order.items:
        items_list.append({
            "product": item.accessory.name,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "total": item.total_price
        })
    
    return {
        "order_number": order.order_number,
        "customer_name": order.customer_name,
        "customer_email": order.customer_email,
        "customer_phone": order.customer_phone,
        "shipping_address": order.shipping_address,
        "items": items_list,
        "total_amount": order.total_amount,
        "currency": order.currency,
        "order_date": order.created_at.strftime("%Y-%m-%d %H:%M:%S")
    }


def _send_email_notification(vendor: Vendor, order: AccessoryOrder, summary: dict) -> None:
    """
    UC004D: Send email notification to vendor with order details and PDF invoice.
    """
    # In production, integrate with email service (SendGrid, AWS SES, etc.)
    email_subject = f"New Order: {order.order_number}"
    
    items_html = "".join([
        f"<tr><td>{item['product']}</td><td>{item['quantity']}</td>" 
        f"<td>₹{item['unit_price']}</td><td>₹{item['total']}</td></tr>"
        for item in summary['items']
    ])
    
    html_content = f"""
    <html>
    <body>
    <h2>New Order Received: {order.order_number}</h2>
    
    <h3>Customer Details:</h3>
    <p>Name: {order.customer_name}</p>
    <p>Email: {order.customer_email}</p>
    <p>Phone: {order.customer_phone}</p>
    <p>Shipping Address: {order.shipping_address}</p>
    
    <h3>Order Items:</h3>
    <table border="1">
    <tr><th>Product</th><th>Quantity</th><th>Unit Price</th><th>Total</th></tr>
    {items_html}
    </table>
    
    <h3>Total Amount: ₹{order.total_amount}</h3>
    
    <p><strong>Disclaimer:</strong> Thar Bengaluru functions only as an intermediary and does not assume responsibility 
    for delivery timelines, product defects, wrong shipments, missing items, packaging damage, warranty disputes, 
    installation concerns, or any other vendor-related issues.</p>
    </body>
    </html>
    """
    
    # Simulate email sending
    print(f"Email notification sent to {vendor.email}: {email_subject}")


def _send_whatsapp_notification(vendor: Vendor, order: AccessoryOrder, summary: dict) -> None:
    """
    UC004D: Send WhatsApp notification to vendor with quick order summary.
    """
    # In production, integrate with WhatsApp Cloud API
    items_text = "\n".join([
        f"• {item['product']} (Qty: {item['quantity']}) - ₹{item['total']}"
        for item in summary['items']
    ])
    
    message = f"""
    🎉 New Order Received! 📦

Order ID: {order.order_number}
Customer: {order.customer_name}
Phone: {order.customer_phone}
Email: {order.customer_email}

📍 Shipping Address:
{order.shipping_address}

📦 Items:
{items_text}

💰 Total Amount: ₹{order.total_amount}
✅ Payment: Confirmed

💡 Disclaimer: Thar Bengaluru functions only as an intermediary.
    """
    
    # Simulate WhatsApp sending
    print(f"WhatsApp notification sent to {vendor.whatsapp_number}: {message}")


# ==================== UC004D: ORDER HISTORY ====================

@router.get("/orders/{order_id}", response_model=AccessoryOrderResponse)
def get_order_details(order_id: int, db: Session = Depends(get_db)):
    """UC004D: Get order details by order ID."""
    order = db.query(AccessoryOrder).filter(AccessoryOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


@router.get("/orders", response_model=List[AccessoryOrderResponse])
def get_user_orders(
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """UC004D: Get user's accessory orders."""
    orders = db.query(AccessoryOrder).filter(
        AccessoryOrder.user_id == current_user.id
    ).order_by(AccessoryOrder.created_at.desc()).offset(skip).limit(limit).all()
    return orders


@router.get("/{accessory_id}", response_model=AccessoryDetailResponse)
def get_accessory(accessory_id: int, db: Session = Depends(get_db)):
    """Get single accessory details with vendor information."""
    accessory = db.query(Accessory).filter(Accessory.id == accessory_id).first()
    if not accessory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accessory not found")
    return accessory

