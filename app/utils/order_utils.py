"""
Order Utilities
Centralized order processing logic for accessories and merchandise.
"""

from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status


def generate_order_number(prefix: str) -> str:
    """
    Generate unique order number with format: PREFIX-YYYYMMDD-XXXX
    
    Args:
        prefix: Order prefix like "ACCS" for accessories or "MERCH" for merchandise
        
    Returns:
        Formatted order number string
        
    Example:
        >>> generate_order_number("ACCS")
        "ACCS-20260308-0001"
    """
    valid_prefixes = {"ACCS", "MERCH"}
    if prefix not in valid_prefixes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid order prefix '{prefix}'. Expected one of: {', '.join(sorted(valid_prefixes))}."
        )

    date_str = datetime.now().strftime("%Y%m%d")
    # Use microseconds to reduce collision risk for rapid successive checkouts.
    counter = int(datetime.now().strftime("%f")) % 10000
    return f"{prefix}-{date_str}-{counter:04d}"


def validate_stock(items: List[Dict[str, Any]], db: Session, model_class) -> None:
    """
    Validate that all items have sufficient stock.
    
    Args:
        items: List of items with 'id' and 'quantity' keys
        db: Database session
        model_class: SQLAlchemy model class (Accessory or Merchandise)
        
    Raises:
        HTTPException: If any item is out of stock or insufficient quantity
        
    Example:
        >>> validate_stock(
        ...     items=[{"id": 1, "quantity": 2}, {"id": 2, "quantity": 3}],
        ...     db=db,
        ...     model_class=Accessory
        ... )
    """
    for item in items:
        product_id = item.get('accessory_id') or item.get('merchandise_id') or item.get('id')
        quantity = item.get('quantity', 1)
        
        product = db.query(model_class).filter(model_class.id == product_id).first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found"
            )
        
        if product.stock < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{product.name}: Only {product.stock} units available (requested: {quantity})"
            )


def prepare_order_summary(order: Any) -> Dict[str, Any]:
    """
    Prepare order summary dict for notifications and invoices.
    Works with both AccessoryOrder and MerchandiseOrder.
    
    Args:
        order: Order model instance (AccessoryOrder or MerchandiseOrder)
        
    Returns:
        Dictionary with order details formatted for display
        
    Example:
        >>> summary = prepare_order_summary(order)
        >>> print(summary['order_number'])
        "ACCS-20260308-0001"
    """
    items_list = []
    
    for item in order.items:
        # Handle both accessory and merchandise items
        product = getattr(item, 'accessory', None) or getattr(item, 'merchandise', None)
        
        item_dict = {
            "product": product.name if product else "Unknown Product",
            "quantity": item.quantity,
            "unit_price": float(item.unit_price),
            "total": float(item.total_price)
        }
        
        # Add size/color if merchandise
        if hasattr(item, 'selected_size') and item.selected_size:
            item_dict["size"] = item.selected_size
        if hasattr(item, 'selected_color') and item.selected_color:
            item_dict["color"] = item.selected_color
            
        items_list.append(item_dict)
    
    return {
        "order_number": order.order_number,
        "order_id": order.id,
        "customer_name": order.customer_name,
        "customer_email": order.customer_email,
        "customer_phone": order.customer_phone,
        "shipping_address": order.shipping_address,
        "items": items_list,
        "total_amount": float(order.total_amount),
        "currency": order.currency,
        "order_date": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "notes": order.notes if hasattr(order, 'notes') else None
    }


def calculate_total_amount(items: List[Dict[str, Any]], db: Session, model_class) -> float:
    """
    Calculate total order amount from items list.
    
    Args:
        items: List of items with 'id' and 'quantity' keys
        db: Database session
        model_class: SQLAlchemy model class (Accessory or Merchandise)
        
    Returns:
        Total amount as float
        
    Example:
        >>> total = calculate_total_amount(
        ...     items=[{"id": 1, "quantity": 2}],
        ...     db=db,
        ...     model_class=Accessory
        ... )
    """
    total = 0.0
    
    for item in items:
        product_id = item.get('accessory_id') or item.get('merchandise_id') or item.get('id')
        quantity = item.get('quantity', 1)
        
        product = db.query(model_class).filter(model_class.id == product_id).first()
        if product:
            # Use discounted price if available
            price = getattr(product, 'discounted_price', None) or product.price
            total += price * quantity
    
    return total


def update_inventory_after_payment(order: Any, db: Session) -> None:
    """
    Deduct inventory stock after successful payment.
    
    Args:
        order: Order model instance with items relationship
        db: Database session
        
    Example:
        >>> update_inventory_after_payment(order, db)
    """
    for order_item in order.items:
        product = getattr(order_item, 'accessory', None) or getattr(order_item, 'merchandise', None)
        if product:
            product.stock -= order_item.quantity
    
    db.commit()
