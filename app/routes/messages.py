from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.database import get_db
from app.models.models import User, Message
from app.routes.auth import get_current_user
from datetime import datetime

router = APIRouter(prefix="/messages", tags=["messages"])


# ==================== Messaging ====================

@router.post("", response_model=dict)
def send_message(
    message_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message to another member."""
    if current_user.is_banned:
        raise HTTPException(status_code=403, detail="Your account is banned and cannot send messages")
    
    receiver_id = message_data.get("receiver_id")
    content = message_data.get("content", "").strip()
    
    if not content:
        raise HTTPException(status_code=400, detail="Message content cannot be empty")
    
    receiver = db.query(User).filter(User.id == receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Recipient not found")
    
    if receiver.is_banned:
        raise HTTPException(status_code=400, detail="Cannot message banned users")
    
    try:
        message = Message(
            sender_id=current_user.id,
            receiver_id=receiver_id,
            content=content,
            is_read=False
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        
        return {
            "id": message.id,
            "sender_id": message.sender_id,
            "receiver_id": message.receiver_id,
            "content": message.content,
            "is_read": message.is_read,
            "created_at": message.created_at,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to send message: {str(e)}")


@router.get("/conversation/{member_id}", response_model=list)
def get_conversation(
    member_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get conversation history with a specific member."""
    if current_user.is_banned:
        raise HTTPException(status_code=403, detail="Your account is banned")
    
    member = db.query(User).filter(User.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Get all messages between current user and the other member
    messages = db.query(Message).filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.receiver_id == member_id),
            and_(Message.sender_id == member_id, Message.receiver_id == current_user.id)
        )
    ).order_by(Message.created_at.desc()).offset(skip).limit(limit).all()
    
    # Mark received messages as read
    unread = db.query(Message).filter(
        Message.receiver_id == current_user.id,
        Message.sender_id == member_id,
        Message.is_read == False
    ).all()
    for msg in unread:
        msg.is_read = True
    db.commit()
    
    return [
        {
            "id": m.id,
            "sender_id": m.sender_id,
            "receiver_id": m.receiver_id,
            "content": m.content,
            "is_read": m.is_read,
            "created_at": m.created_at,
        }
        for m in reversed(messages)  # Return in chronological order
    ]


@router.get("/conversations", response_model=list)
def get_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of active conversations for current user."""
    if current_user.is_banned:
        raise HTTPException(status_code=403, detail="Your account is banned")
    
    # Get all unique members the user has conversed with
    from sqlalchemy import func, distinct
    
    members_ids = db.query(
        func.distinct(
            func.coalesce(Message.sender_id, Message.receiver_id)
        )
    ).filter(
        or_(
            Message.sender_id == current_user.id,
            Message.receiver_id == current_user.id
        )
    ).all()
    
    conversation_members = []
    for member_tuple in members_ids:
        member_id = member_tuple[0]
        if member_id != current_user.id:
            conversation_members.append(member_id)
    
    # Get last message in each conversation
    conversations = []
    for member_id in conversation_members[:limit]:
        last_message = db.query(Message).filter(
            or_(
                and_(Message.sender_id == current_user.id, Message.receiver_id == member_id),
                and_(Message.sender_id == member_id, Message.receiver_id == current_user.id)
            )
        ).order_by(Message.created_at.desc()).first()
        
        member = db.query(User).filter(User.id == member_id).first()
        if member:
            unread_count = db.query(Message).filter(
                Message.sender_id == member_id,
                Message.receiver_id == current_user.id,
                Message.is_read == False
            ).count()
            
            conversations.append({
                "member_id": member.id,
                "member_name": member.name,
                "last_message": last_message.content if last_message else None,
                "last_message_time": last_message.created_at if last_message else None,
                "unread_count": unread_count,
            })
    
    return conversations


@router.get("/{message_id}", response_model=dict)
def get_message(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific message by ID."""
    message = db.query(Message).filter(Message.id == message_id).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Only sender and receiver can view the message
    if message.sender_id != current_user.id and message.receiver_id != current_user.id:
        raise HTTPException(status_code=403, detail="You don't have access to this message")
    
    return {
        "id": message.id,
        "sender_id": message.sender_id,
        "receiver_id": message.receiver_id,
        "content": message.content,
        "is_read": message.is_read,
        "created_at": message.created_at,
    }


@router.delete("/{message_id}", status_code=204)
def delete_message(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a message (only sender can delete)."""
    message = db.query(Message).filter(Message.id == message_id).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    if message.sender_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only sender can delete this message")
    
    db.delete(message)
    db.commit()
    return None

