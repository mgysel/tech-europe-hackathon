"""
Utility functions for the AI Hackathon Backend
"""
from typing import Dict, Any, Optional, List
from firebase_admin import firestore
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def validate_order_data(order_data: Dict[str, Any]) -> bool:
    """
    Validate order data structure
    
    Args:
        order_data: Dictionary containing order information
        
    Returns:
        bool: True if valid, False otherwise
    """
    required_fields = ['order_id', 'customer_id', 'items', 'total']
    
    for field in required_fields:
        if field not in order_data:
            logger.error(f"Missing required field: {field}")
            return False
    
    # Validate items is a list
    if not isinstance(order_data['items'], list):
        logger.error("Items must be a list")
        return False
    
    # Validate total is a number
    if not isinstance(order_data['total'], (int, float)):
        logger.error("Total must be a number")
        return False
    
    return True

def create_order_document(db: firestore.Client, order_data: Dict[str, Any]) -> bool:
    """
    Create a new order document in Firebase
    
    Args:
        db: Firebase client
        order_data: Order data dictionary
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not validate_order_data(order_data):
            return False
        
        # Add timestamps
        order_data['created_at'] = firestore.SERVER_TIMESTAMP
        order_data['updated_at'] = firestore.SERVER_TIMESTAMP
        order_data['status'] = 'pending'
        
        # Create document
        doc_ref = db.collection('orders').document(order_data['order_id'])
        doc_ref.set(order_data)
        
        logger.info(f"Order {order_data['order_id']} created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        return False

def get_order_by_id(db: firestore.Client, order_id: str) -> Optional[Dict[str, Any]]:
    """
    Get order by ID from Firebase
    
    Args:
        db: Firebase client
        order_id: Order ID to retrieve
        
    Returns:
        Optional[Dict]: Order data if found, None otherwise
    """
    try:
        doc_ref = db.collection('orders').document(order_id)
        doc = doc_ref.get()
        
        if doc.exists:
            return doc.to_dict()
        else:
            logger.warning(f"Order {order_id} not found")
            return None
            
    except Exception as e:
        logger.error(f"Error retrieving order {order_id}: {e}")
        return None

def update_order_field(db: firestore.Client, order_id: str, field: str, value: Any) -> bool:
    """
    Update a specific field in an order document
    
    Args:
        db: Firebase client
        order_id: Order ID to update
        field: Field name to update
        value: New value for the field
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        doc_ref = db.collection('orders').document(order_id)
        
        update_data = {
            field: value,
            'updated_at': firestore.SERVER_TIMESTAMP
        }
        
        doc_ref.update(update_data)
        
        logger.info(f"Order {order_id} field '{field}' updated successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error updating order {order_id}: {e}")
        return False

def get_orders_by_status(db: firestore.Client, status: str) -> List[Dict[str, Any]]:
    """
    Get all orders with a specific status
    
    Args:
        db: Firebase client
        status: Status to filter by
        
    Returns:
        List[Dict]: List of orders with the specified status
    """
    try:
        orders_ref = db.collection('orders')
        query = orders_ref.where('status', '==', status)
        docs = query.stream()
        
        orders = []
        for doc in docs:
            order_data = doc.to_dict()
            orders.append(order_data)
        
        logger.info(f"Retrieved {len(orders)} orders with status '{status}'")
        return orders
        
    except Exception as e:
        logger.error(f"Error retrieving orders with status '{status}': {e}")
        return []

def delete_order(db: firestore.Client, order_id: str) -> bool:
    """
    Delete an order from Firebase
    
    Args:
        db: Firebase client
        order_id: Order ID to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        doc_ref = db.collection('orders').document(order_id)
        doc_ref.delete()
        
        logger.info(f"Order {order_id} deleted successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting order {order_id}: {e}")
        return False

def format_order_response(order_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format order data for API response
    
    Args:
        order_data: Raw order data from Firebase
        
    Returns:
        Dict: Formatted order data
    """
    if not order_data:
        return {}
    
    # Convert Firestore timestamps to ISO format strings
    formatted_data = order_data.copy()
    
    for field in ['created_at', 'updated_at']:
        if field in formatted_data and formatted_data[field]:
            if hasattr(formatted_data[field], 'isoformat'):
                formatted_data[field] = formatted_data[field].isoformat()
    
    return formatted_data

def calculate_order_total(items: List[Dict[str, Any]]) -> float:
    """
    Calculate total order amount from items
    
    Args:
        items: List of order items with price and quantity
        
    Returns:
        float: Total order amount
    """
    total = 0.0
    
    for item in items:
        price = item.get('price', 0)
        quantity = item.get('quantity', 1)
        total += price * quantity
    
    return round(total, 2) 