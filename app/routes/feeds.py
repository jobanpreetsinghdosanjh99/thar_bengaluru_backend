from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.models import Feed, FeedComment, User
from app.schemas.schemas import FeedCreate, FeedResponse, FeedListResponse, FeedCommentCreate, FeedCommentResponse
from app.routes.auth import get_current_user

router = APIRouter(prefix="/feeds", tags=["feeds"])


@router.post("", response_model=FeedResponse)
def create_feed(feed_data: FeedCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new community feed post."""
    new_feed = Feed(
        author_id=current_user.id,
        title=feed_data.title,
        content=feed_data.content,
        image_url=feed_data.image_url
    )
    db.add(new_feed)
    db.commit()
    db.refresh(new_feed)
    return new_feed


@router.get("", response_model=List[FeedListResponse])
def list_feeds(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """Get list of community feeds."""
    feeds = db.query(Feed).order_by(Feed.created_at.desc()).offset(skip).limit(limit).all()
    return feeds


@router.get("/{feed_id}", response_model=FeedResponse)
def get_feed(feed_id: int, db: Session = Depends(get_db)):
    """Get single feed with comments."""
    feed = db.query(Feed).filter(Feed.id == feed_id).first()
    if not feed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feed not found")
    return feed


@router.post("/{feed_id}/comments", response_model=FeedCommentResponse)
def add_comment(
    feed_id: int,
    comment_data: FeedCommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a comment to a feed post."""
    feed = db.query(Feed).filter(Feed.id == feed_id).first()
    if not feed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feed not found")
    
    new_comment = FeedComment(
        feed_id=feed_id,
        author_id=current_user.id,
        content=comment_data.content
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment


@router.get("/{feed_id}/comments", response_model=List[FeedCommentResponse])
def list_comments(feed_id: int, db: Session = Depends(get_db)):
    """Get comments for a feed post."""
    comments = db.query(FeedComment).filter(FeedComment.feed_id == feed_id).all()
    return comments
