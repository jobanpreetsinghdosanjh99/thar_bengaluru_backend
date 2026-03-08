"""
Notification Utilities
Centralized email and WhatsApp notification logic.
"""

import os
from typing import Dict, Any, Optional
from app.models.models import Vendor, User


def send_vendor_email(vendor: Vendor, order_summary: Dict[str, Any], product_type: str = "Product") -> bool:
    """
    Send email notification to vendor with order details.
    
    Args:
        vendor: Vendor model instance
        order_summary: Order summary dict from prepare_order_summary()
        product_type: Type of product ("Accessory" or "Merchandise")
        
    Returns:
        True if email sent successfully, False otherwise
        
    Example:
        >>> send_vendor_email(vendor, order_summary, "Accessory")
    """
    try:
        email_subject = f"New {product_type} Order: {order_summary['order_number']}"
        
        # Build items HTML table
        items_html = "".join([
            f"<tr>"
            f"<td>{item['product']}</td>"
            f"<td>{item['quantity']}</td>"
            f"<td>₹{item['unit_price']:.2f}</td>"
            f"<td>₹{item['total']:.2f}</td>"
            f"</tr>"
            for item in order_summary['items']
        ])
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #FF9800; border-bottom: 2px solid #FF9800; padding-bottom: 10px;">
                    🎉 New {product_type} Order Received!
                </h2>
                
                <div style="background-color: #f5f5f5; padding: 15px; margin: 20px 0; border-radius: 5px;">
                    <h3 style="margin-top: 0; color: #555;">Order Details</h3>
                    <p><strong>Order Number:</strong> {order_summary['order_number']}</p>
                    <p><strong>Order Date:</strong> {order_summary['order_date']}</p>
                    <p><strong>Total Amount:</strong> <span style="color: #FF9800; font-size: 18px; font-weight: bold;">₹{order_summary['total_amount']:.2f}</span></p>
                </div>
                
                <div style="margin: 20px 0;">
                    <h3 style="color: #555;">Customer Information</h3>
                    <p><strong>Name:</strong> {order_summary['customer_name']}</p>
                    <p><strong>Email:</strong> {order_summary['customer_email']}</p>
                    <p><strong>Phone:</strong> {order_summary['customer_phone']}</p>
                    <p><strong>Shipping Address:</strong><br>{order_summary['shipping_address']}</p>
                </div>
                
                <div style="margin: 20px 0;">
                    <h3 style="color: #555;">Order Items</h3>
                    <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                        <thead>
                            <tr style="background-color: #FF9800; color: white;">
                                <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Product</th>
                                <th style="padding: 10px; text-align: center; border: 1px solid #ddd;">Qty</th>
                                <th style="padding: 10px; text-align: right; border: 1px solid #ddd;">Unit Price</th>
                                <th style="padding: 10px; text-align: right; border: 1px solid #ddd;">Total</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items_html}
                            <tr style="background-color: #f0f0f0; font-weight: bold;">
                                <td colspan="3" style="padding: 10px; text-align: right; border: 1px solid #ddd;">Total Amount:</td>
                                <td style="padding: 10px; text-align: right; border: 1px solid #ddd; color: #FF9800;">₹{order_summary['total_amount']:.2f}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                
                {f"<div style='background-color: #fff3cd; padding: 15px; margin: 20px 0; border-left: 4px solid #ffc107; border-radius: 5px;'><p><strong>Notes:</strong> {order_summary['notes']}</p></div>" if order_summary.get('notes') else ""}
                
                <div style="background-color: #e8f5e9; padding: 15px; margin: 20px 0; border-left: 4px solid #4caf50; border-radius: 5px;">
                    <p style="margin: 0;"><strong>✅ Payment Status:</strong> Confirmed</p>
                    <p style="margin: 10px 0 0 0; font-size: 14px; color: #666;">Please process this order and update the delivery status.</p>
                </div>
                
                <div style="background-color: #fff3e0; padding: 15px; margin: 20px 0; border-left: 4px solid #ff9800; border-radius: 5px;">
                    <p style="margin: 0; font-size: 12px; color: #666;">
                        <strong>⚠️ Important Disclaimer:</strong> Thar Bengaluru functions only as an intermediary and does not assume 
                        responsibility for delivery timelines, product defects, wrong shipments, missing items, packaging damage, 
                        warranty disputes, installation concerns, or any other vendor-related issues.
                    </p>
                </div>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #999; font-size: 12px;">
                    <p>This is an automated email from Thar Bengaluru Club</p>
                    <p>For support, contact us at support@tharbengaluru.com</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # In production, integrate with email service (SendGrid, AWS SES, SMTP)
        # Example with SMTP:
        # import smtplib
        # from email.mime.text import MIMEText
        # from email.mime.multipart import MIMEMultipart
        #
        # msg = MIMEMultipart('alternative')
        # msg['Subject'] = email_subject
        # msg['From'] = os.getenv('SMTP_FROM_EMAIL', 'noreply@tharbengaluru.com')
        # msg['To'] = vendor.email
        # msg.attach(MIMEText(html_content, 'html'))
        #
        # with smtplib.SMTP(os.getenv('SMTP_HOST'), int(os.getenv('SMTP_PORT', 587))) as server:
        #     server.starttls()
        #     server.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASSWORD'))
        #     server.send_message(msg)
        
        # Development: Log email content
        print(f"📧 Email sent to {vendor.email}:")
        print(f"   Subject: {email_subject}")
        print(f"   Order: {order_summary['order_number']}, Amount: ₹{order_summary['total_amount']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Email notification failed for vendor {vendor.id}: {str(e)}")
        return False


def send_vendor_whatsapp(vendor: Vendor, order_summary: Dict[str, Any], product_type: str = "Product") -> bool:
    """
    Send WhatsApp notification to vendor with order summary.
    
    Args:
        vendor: Vendor model instance
        order_summary: Order summary dict from prepare_order_summary()
        product_type: Type of product ("Accessory" or "Merchandise")
        
    Returns:
        True if WhatsApp sent successfully, False otherwise
        
    Example:
        >>> send_vendor_whatsapp(vendor, order_summary, "Merchandise")
    """
    try:
        if not vendor.whatsapp_number:
            print(f"⚠️ No WhatsApp number for vendor {vendor.id}")
            return False
        
        # Build items text
        items_text = "\n".join([
            f"  • {item['product']} (Qty: {item['quantity']}) - ₹{item['total']:.2f}"
            for item in order_summary['items']
        ])
        
        # Add size/color info if available
        items_detailed = "\n".join([
            f"  • {item['product']}" + 
            (f" [{item.get('size', '')}]" if item.get('size') else "") +
            (f" ({item.get('color', '')})" if item.get('color') else "") +
            f" x{item['quantity']} - ₹{item['total']:.2f}"
            for item in order_summary['items']
        ])
        
        message = f"""
🎉 *New {product_type} Order Received!* 📦

*Order ID:* {order_summary['order_number']}
*Date:* {order_summary['order_date']}
*Amount:* ₹{order_summary['total_amount']:.2f} ✅

👤 *Customer Details:*
  Name: {order_summary['customer_name']}
  Phone: {order_summary['customer_phone']}
  Email: {order_summary['customer_email']}

📍 *Shipping Address:*
{order_summary['shipping_address']}

📦 *Items:*
{items_detailed}

💰 *Total Amount:* ₹{order_summary['total_amount']:.2f}
✅ *Payment:* Confirmed

{f"📝 *Notes:* {order_summary['notes']}" if order_summary.get('notes') else ""}

---
⚠️ *Disclaimer:* Thar Bengaluru functions only as an intermediary and is not responsible for delivery, product quality, or vendor-related issues.
        """.strip()
        
        # In production, integrate with WhatsApp Cloud API
        # Example:
        # import requests
        # WHATSAPP_API_URL = os.getenv('WHATSAPP_API_URL')
        # WHATSAPP_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
        # WHATSAPP_PHONE_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        #
        # url = f"{WHATSAPP_API_URL}/{WHATSAPP_PHONE_ID}/messages"
        # headers = {
        #     "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        #     "Content-Type": "application/json"
        # }
        # data = {
        #     "messaging_product": "whatsapp",
        #     "to": vendor.whatsapp_number,
        #     "type": "text",
        #     "text": {"body": message}
        # }
        # response = requests.post(url, headers=headers, json=data)
        # response.raise_for_status()
        
        # Development: Log WhatsApp message
        print(f"💬 WhatsApp sent to {vendor.whatsapp_number}:")
        print(f"   Order: {order_summary['order_number']}")
        print(f"   Message: {len(message)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ WhatsApp notification failed for vendor {vendor.id}: {str(e)}")
        return False


def send_user_confirmation(user_email: str, order_summary: Dict[str, Any], product_type: str = "Product") -> bool:
    """
    Send order confirmation email to customer.
    
    Args:
        user_email: Customer email address
        order_summary: Order summary dict from prepare_order_summary()
        product_type: Type of product ("Accessory" or "Merchandise")
        
    Returns:
        True if email sent successfully, False otherwise
        
    Example:
        >>> send_user_confirmation("customer@example.com", order_summary, "Accessory")
    """
    try:
        email_subject = f"Order Confirmed: {order_summary['order_number']}"
        
        items_html = "".join([
            f"<tr>"
            f"<td style='padding: 8px; border: 1px solid #ddd;'>{item['product']}</td>"
            f"<td style='padding: 8px; border: 1px solid #ddd; text-align: center;'>{item['quantity']}</td>"
            f"<td style='padding: 8px; border: 1px solid #ddd; text-align: right;'>₹{item['total']:.2f}</td>"
            f"</tr>"
            for item in order_summary['items']
        ])
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #FF9800; margin: 0;">THAR Bengaluru</h1>
                    <p style="color: #666; margin: 5px 0;">4x4 Off-Road Club</p>
                </div>
                
                <div style="background-color: #4caf50; color: white; padding: 20px; text-align: center; border-radius: 5px;">
                    <h2 style="margin: 0;">✓ Order Confirmed!</h2>
                    <p style="margin: 10px 0 0 0; font-size: 16px;">Thank you for your order</p>
                </div>
                
                <div style="background-color: #f5f5f5; padding: 15px; margin: 20px 0; border-radius: 5px;">
                    <p style="margin: 0;"><strong>Order Number:</strong> <span style="color: #FF9800; font-size: 18px;">{order_summary['order_number']}</span></p>
                    <p style="margin: 10px 0 0 0;"><strong>Order Date:</strong> {order_summary['order_date']}</p>
                </div>
                
                <h3 style="color: #555;">Order Summary</h3>
                <table style="width: 100%; border-collapse: collapse; margin: 10px 0;">
                    <thead>
                        <tr style="background-color: #f0f0f0;">
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Product</th>
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: center;">Qty</th>
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: right;">Amount</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items_html}
                        <tr style="background-color: #fff3e0; font-weight: bold;">
                            <td colspan="2" style="padding: 10px; border: 1px solid #ddd; text-align: right;">Total:</td>
                            <td style="padding: 10px; border: 1px solid #ddd; text-align: right; color: #FF9800; font-size: 18px;">₹{order_summary['total_amount']:.2f}</td>
                        </tr>
                    </tbody>
                </table>
                
                <h3 style="color: #555;">Shipping Address</h3>
                <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px;">
                    <p style="margin: 0;">{order_summary['shipping_address']}</p>
                </div>
                
                <div style="background-color: #e3f2fd; padding: 15px; margin: 20px 0; border-left: 4px solid #2196f3; border-radius: 5px;">
                    <p style="margin: 0;"><strong>📦 What's Next?</strong></p>
                    <ul style="margin: 10px 0; padding-left: 20px;">
                        <li>Vendor has been notified of your order</li>
                        <li>You'll receive shipping updates via email</li>
                        <li>Track your order status in the app</li>
                    </ul>
                </div>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #999; font-size: 12px;">
                    <p>Need help? Contact us at support@tharbengaluru.com</p>
                    <p>© 2026 THAR Bengaluru. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Development: Log confirmation email
        print(f"📧 Order confirmation sent to {user_email}:")
        print(f"   Order: {order_summary['order_number']}")
        
        return True
        
    except Exception as e:
        print(f"❌ User confirmation email failed: {str(e)}")
        return False


def notify_vendor_complete(vendor: Vendor, order_summary: Dict[str, Any], product_type: str = "Product") -> Dict[str, bool]:
    """
    Send both email and WhatsApp notifications to vendor.
    
    Args:
        vendor: Vendor model instance
        order_summary: Order summary dict
        product_type: Type of product
        
    Returns:
        Dictionary with email_sent and whatsapp_sent boolean flags
        
    Example:
        >>> result = notify_vendor_complete(vendor, order_summary, "Accessory")
        >>> print(f"Email: {result['email_sent']}, WhatsApp: {result['whatsapp_sent']}")
    """
    return {
        "email_sent": send_vendor_email(vendor, order_summary, product_type),
        "whatsapp_sent": send_vendor_whatsapp(vendor, order_summary, product_type)
    }
