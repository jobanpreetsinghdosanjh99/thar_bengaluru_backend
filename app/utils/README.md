# Utilities Module

Centralized utility functions for common functionalities (payment, notifications, order processing) to avoid code duplication across routes.

## 📁 Module Structure

```
app/utils/
├── __init__.py              # Module exports
├── order_utils.py           # Order processing utilities
├── notification_utils.py    # Email & WhatsApp notifications
└── payment_utils.py         # Payment gateway integration
```

## 🛠️ Usage

### Order Utilities

```python
from app.utils import (
    generate_order_number,
    validate_stock,
    prepare_order_summary,
    calculate_total_amount,
    update_inventory_after_payment
)

# Generate unique order number
order_number = generate_order_number("ACCS")  # → "ACCS-20260308-0001"
order_number = generate_order_number("MERCH") # → "MERCH-20260308-0002"

# Validate stock before checkout
validate_stock(
    items=[{"accessory_id": 1, "quantity": 2}],
    db=db,
    model_class=Accessory
)

# Prepare order summary for notifications
summary = prepare_order_summary(order)
# → Returns dict with order_number, customer details, items, total_amount, etc.

# Calculate total from items
total = calculate_total_amount(items, db, Accessory)

# Update inventory after successful payment
update_inventory_after_payment(order, db)
```

### Notification Utilities

```python
from app.utils import (
    send_vendor_email,
    send_vendor_whatsapp,
    send_user_confirmation,
    notify_vendor_complete
)

# Send email to vendor
send_vendor_email(vendor, order_summary, "Accessory")

# Send WhatsApp to vendor
send_vendor_whatsapp(vendor, order_summary, "Merchandise")

# Send confirmation email to customer
send_user_confirmation("customer@example.com", order_summary, "Accessory")

# Send both email + WhatsApp to vendor
result = notify_vendor_complete(vendor, order_summary, "Merchandise")
# → Returns {"email_sent": True, "whatsapp_sent": True}
```

### Payment Utilities

```python
from app.utils import (
    create_payment_redirect,
    process_payment_success,
    process_payment_failure,
    verify_payment_signature
)

# Create payment redirect URL
redirect = create_payment_redirect(
    order_id=123,
    order_number="ACCS-20260308-0001",
    amount=2500.0,
    customer_email="john@example.com",
    customer_phone="9876543210",
    customer_name="John Doe",
    gateway="razorpay"
)
# → Returns {"payment_url": "...", "order_id": 123, "amount": 2500.0, ...}

# Process successful payment
result = process_payment_success(order, db)
# → Updates order status, deducts inventory, returns success message

# Process failed payment
result = process_payment_failure(order, db, "Insufficient funds")
# → Updates order status without touching inventory

# Verify payment signature (security)
is_valid = verify_payment_signature(order_id, payment_id, signature, "razorpay")
```

## 🔧 Integration in Routes

### Before (Duplicated Code)

```python
# In accessories.py
def _generate_order_number():
    date_str = datetime.now().strftime("%Y%m%d")
    # ... duplicated logic

def _send_vendor_notifications(order, db):
    # ... duplicated email logic
    # ... duplicated WhatsApp logic

# In merchandise.py
def _generate_merchandise_order_number():
    date_str = datetime.now().strftime("%Y%m%d")
    # ... SAME logic duplicated
```

### After (Centralized Utilities)

```python
from app.utils import (
    generate_order_number,
    validate_stock,
    prepare_order_summary,
    create_payment_redirect,
    process_payment_success,
    notify_vendor_complete
)

@router.post("/checkout")
def checkout(checkout_data: CheckoutRequest, db: Session = Depends(get_db)):
    # Validate stock
    validate_stock(checkout_data.items, db, Accessory)
    
    # Generate order number
    order_number = generate_order_number("ACCS")
    
    # Create order
    order = AccessoryOrder(order_number=order_number, ...)
    db.add(order)
    db.commit()
    
    # Create payment redirect
    redirect = create_payment_redirect(
        order_id=order.id,
        order_number=order.order_number,
        amount=order.total_amount,
        customer_email=checkout_data.customer_email,
        customer_phone=checkout_data.customer_phone,
        customer_name=checkout_data.customer_name
    )
    
    return redirect

@router.post("/payment/success/{order_id}")
def payment_success(order_id: int, db: Session = Depends(get_db)):
    order = db.query(AccessoryOrder).get(order_id)
    
    # Process payment
    result = process_payment_success(order, db)
    
    # Send notifications
    summary = prepare_order_summary(order)
    notify_result = notify_vendor_complete(order.vendor, summary, "Accessory")
    
    # Update notification flags
    if notify_result['email_sent']:
        order.vendor_notification_sent = True
        order.order_status = OrderStatus.VENDOR_NOTIFIED
        db.commit()
    
    return result
```

## 🌍 Environment Variables

### Email Configuration (notification_utils.py)
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@tharbengaluru.com
SMTP_FROM_NAME=THAR Bengaluru
```

### WhatsApp Configuration (notification_utils.py)
```env
WHATSAPP_API_URL=https://graph.facebook.com/v17.0
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_ACCESS_TOKEN=your_whatsapp_token
```

### Payment Gateway Configuration (payment_utils.py)
```env
# Razorpay
RAZORPAY_KEY_ID=rzp_live_xxxxx
RAZORPAY_KEY_SECRET=your_secret_key

# PhonePe
PHONEPE_MERCHANT_ID=YOUR_MERCHANT_ID
PHONEPE_SALT_KEY=your_salt_key
PHONEPE_SALT_INDEX=1

# Backend URL for callbacks
BACKEND_URL=https://api.tharbengaluru.com
```

## ✅ Benefits

1. **No Code Duplication**: Single source of truth for common logic
2. **Easy Maintenance**: Fix bugs in one place, applies everywhere
3. **Consistent Behavior**: Same logic across accessories, merchandise, and future modules
4. **Testable**: Utilities can be unit tested independently
5. **Flexible**: Easy to switch payment gateways or notification services
6. **Production Ready**: Comments include actual integration code for production

## 🚀 Future Extensions

- Add SMS notification utilities
- Support multiple payment gateways with auto-selection
- PDF invoice generation utilities
- Order tracking and status update utilities
- Refund processing utilities
- Analytics and reporting utilities

## 📝 Notes

- All functions include detailed docstrings with examples
- Error handling and logging included
- Mock implementations for development
- Production integration code provided in comments
- Works with both AccessoryOrder and MerchandiseOrder models
