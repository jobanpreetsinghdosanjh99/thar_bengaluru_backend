"""
Payment Utilities
Centralized payment gateway integration logic for Razorpay, PhonePe, etc.
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.models import PaymentStatus, OrderStatus


def create_payment_redirect(
    order_id: int,
    order_number: str,
    amount: float,
    customer_email: str,
    customer_phone: str,
    customer_name: str,
    vendor_gateway_url: Optional[str] = None,
    gateway: str = "razorpay"
) -> Dict[str, Any]:
    """
    Create payment gateway redirect URL for order.
    
    Args:
        order_id: Order ID from database
        order_number: Formatted order number (e.g., "ACCS-20260308-0001")
        amount: Total order amount in INR
        customer_email: Customer email address
        customer_phone: Customer phone number
        customer_name: Customer full name
        vendor_gateway_url: Optional vendor-specific payment URL
        gateway: Payment gateway name ("razorpay", "phonepe", etc.)
        
    Returns:
        Dictionary with payment_url, gateway info, and order details
        
    Example:
        >>> redirect = create_payment_redirect(
        ...     order_id=123,
        ...     order_number="ACCS-20260308-0001",
        ...     amount=2500.0,
        ...     customer_email="customer@example.com",
        ...     customer_phone="9876543210",
        ...     customer_name="John Doe"
        ... )
        >>> print(redirect['payment_url'])
    """
    try:
        # Use vendor gateway URL if provided, otherwise use default
        if vendor_gateway_url:
            payment_url = f"{vendor_gateway_url}?order_id={order_id}&amount={amount}&email={customer_email}"
        else:
            # In production, integrate with actual payment gateways
            if gateway.lower() == "razorpay":
                payment_url = _create_razorpay_payment(
                    order_id, order_number, amount, customer_email, customer_phone, customer_name
                )
            elif gateway.lower() == "phonepe":
                payment_url = _create_phonepe_payment(
                    order_id, order_number, amount, customer_email, customer_phone, customer_name
                )
            else:
                # Fallback to mock payment URL
                payment_url = f"https://payment.tharbengaluru.com/pay?order={order_number}&amount={amount}"
        
        return {
            "order_id": order_id,
            "order_number": order_number,
            "payment_url": payment_url,
            "gateway": gateway,
            "amount": amount,
            "currency": "INR",
            "customer_email": customer_email,
            "customer_phone": customer_phone
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment redirect: {str(e)}"
        )


def _create_razorpay_payment(
    order_id: int,
    order_number: str,
    amount: float,
    customer_email: str,
    customer_phone: str,
    customer_name: str
) -> str:
    """
    Create Razorpay payment URL.
    
    In production, this would use razorpay Python SDK:
    
    import razorpay
    client = razorpay.Client(auth=(os.getenv('RAZORPAY_KEY_ID'), os.getenv('RAZORPAY_KEY_SECRET')))
    
    order_data = {
        'amount': int(amount * 100),  # Amount in paise
        'currency': 'INR',
        'receipt': order_number,
        'notes': {
            'order_id': order_id,
            'customer_email': customer_email
        }
    }
    
    razorpay_order = client.order.create(data=order_data)
    payment_url = f"https://razorpay.com/checkout?order_id={razorpay_order['id']}"
    """
    # Development mock URL
    razorpay_key = os.getenv('RAZORPAY_KEY_ID', 'rzp_test_mock')
    return f"https://api.razorpay.com/v1/checkout/embedded?order_id={order_number}&amount={int(amount * 100)}&key={razorpay_key}"


def _create_phonepe_payment(
    order_id: int,
    order_number: str,
    amount: float,
    customer_email: str,
    customer_phone: str,
    customer_name: str
) -> str:
    """
    Create PhonePe payment URL.
    
    In production, this would use PhonePe Payment Gateway API:
    
    import hashlib
    import base64
    import requests
    
    merchant_id = os.getenv('PHONEPE_MERCHANT_ID')
    salt_key = os.getenv('PHONEPE_SALT_KEY')
    salt_index = os.getenv('PHONEPE_SALT_INDEX', '1')
    
    payload = {
        'merchantId': merchant_id,
        'merchantTransactionId': order_number,
        'amount': int(amount * 100),  # Amount in paise
        'merchantUserId': f'USER_{order_id}',
        'callbackUrl': f'{os.getenv("BACKEND_URL")}/accessories/payment/success/{order_id}',
        'mobileNumber': customer_phone,
        'deviceContext': {'deviceOS': 'WEB'},
        'paymentInstrument': {'type': 'PAY_PAGE'}
    }
    
    encoded_payload = base64.b64encode(json.dumps(payload).encode()).decode()
    checksum = hashlib.sha256(f'{encoded_payload}/pg/v1/pay{salt_key}'.encode()).hexdigest() + '###' + salt_index
    
    response = requests.post(
        'https://api.phonepe.com/apis/hermes/pg/v1/pay',
        json={'request': encoded_payload},
        headers={'X-VERIFY': checksum}
    )
    
    return response.json()['data']['instrumentResponse']['redirectInfo']['url']
    """
    # Development mock URL
    merchant_id = os.getenv('PHONEPE_MERCHANT_ID', 'PHONEPE_MOCK')
    return f"https://mercury-uat.phonepe.com/transact/simulator?order={order_number}&amount={amount}&merchant={merchant_id}"


def process_payment_success(order: Any, db: Session) -> Dict[str, Any]:
    """
    Process successful payment webhook.
    Updates order status, inventory, and triggers notifications.
    
    Args:
        order: Order model instance (AccessoryOrder or MerchandiseOrder)
        db: Database session
        
    Returns:
        Dictionary with success message and order details
        
    Example:
        >>> result = process_payment_success(order, db)
        >>> print(result['message'])
    """
    try:
        # Check if already processed
        if order.payment_status == PaymentStatus.SUCCESS:
            return {
                "message": "Order already processed",
                "order_number": order.order_number,
                "order_id": order.id,
                "already_processed": True
            }
        
        # Update payment and order status
        order.payment_status = PaymentStatus.SUCCESS
        order.order_status = OrderStatus.PAYMENT_SUCCESS
        order.updated_at = datetime.utcnow()
        
        # Deduct inventory stock
        for order_item in order.items:
            product = getattr(order_item, 'accessory', None) or getattr(order_item, 'merchandise', None)
            if product:
                product.stock -= order_item.quantity
        
        db.commit()
        
        return {
            "message": "Payment successful and order confirmed",
            "order_number": order.order_number,
            "order_id": order.id,
            "payment_status": order.payment_status.value,
            "order_status": order.order_status.value,
            "already_processed": False
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment success processing failed: {str(e)}"
        )


def process_payment_failure(order: Any, db: Session, failure_reason: Optional[str] = None) -> Dict[str, Any]:
    """
    Process failed payment webhook.
    Updates order status without affecting inventory.
    
    Args:
        order: Order model instance (AccessoryOrder or MerchandiseOrder)
        db: Database session
        failure_reason: Optional reason for payment failure
        
    Returns:
        Dictionary with failure message and order details
        
    Example:
        >>> result = process_payment_failure(order, db, "Insufficient funds")
        >>> print(result['message'])
    """
    try:
        # Update payment status
        order.payment_status = PaymentStatus.FAILED
        order.order_status = OrderStatus.PAYMENT_FAILED
        order.updated_at = datetime.utcnow()
        
        # Store failure reason if provided
        if failure_reason and hasattr(order, 'notes'):
            existing_notes = order.notes or ""
            order.notes = f"{existing_notes}\nPayment Failure: {failure_reason}".strip()
        
        db.commit()
        
        return {
            "message": "Payment unsuccessful. No charges were made.",
            "order_number": order.order_number,
            "order_id": order.id,
            "payment_status": order.payment_status.value,
            "order_status": order.order_status.value,
            "failure_reason": failure_reason
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment failure processing failed: {str(e)}"
        )


def verify_payment_signature(
    order_id: str,
    payment_id: str,
    signature: str,
    gateway: str = "razorpay"
) -> bool:
    """
    Verify payment gateway signature for security.
    
    Args:
        order_id: Gateway order ID
        payment_id: Payment transaction ID
        signature: Signature from payment gateway
        gateway: Payment gateway name
        
    Returns:
        True if signature is valid, False otherwise
        
    Example:
        >>> is_valid = verify_payment_signature(order_id, payment_id, signature)
    """
    try:
        if gateway.lower() == "razorpay":
            # Razorpay signature verification
            # import hmac
            # import hashlib
            # secret = os.getenv('RAZORPAY_KEY_SECRET')
            # message = f"{order_id}|{payment_id}"
            # generated_signature = hmac.new(
            #     secret.encode(),
            #     message.encode(),
            #     hashlib.sha256
            # ).hexdigest()
            # return generated_signature == signature
            return True  # Mock for development
            
        elif gateway.lower() == "phonepe":
            # PhonePe checksum verification
            # import hashlib
            # salt_key = os.getenv('PHONEPE_SALT_KEY')
            # salt_index = os.getenv('PHONEPE_SALT_INDEX')
            # calculated = hashlib.sha256(f'{response_payload}{salt_key}'.encode()).hexdigest() + '###' + salt_index
            # return calculated == signature
            return True  # Mock for development
            
        return True
        
    except Exception as e:
        print(f"❌ Payment signature verification failed: {str(e)}")
        return False
