import re
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import case
from typing import List, Optional
from app.database import get_db
from app.models.models import Feed, FeedComment, FeedLike, User, ClubMembershipRequest, MembershipStatus
from app.schemas.schemas import FeedCreate, FeedResponse, FeedListResponse, FeedCommentCreate, FeedCommentResponse
from app.routes.auth import get_current_user
from app.security import decode_access_token

router = APIRouter(prefix="/feeds", tags=["feeds"])


def _has_active_club_membership(user_id: int, db: Session) -> bool:
    membership = db.query(ClubMembershipRequest).filter(
        ClubMembershipRequest.user_id == user_id,
        ClubMembershipRequest.status == MembershipStatus.APPROVED,
        ClubMembershipRequest.payment_status == "success"
    ).order_by(ClubMembershipRequest.created_at.desc()).first()
    return membership is not None


def _optional_current_user(
    authorization: Optional[str],
    db: Session
) -> Optional[User]:
    if not authorization:
        return None

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
    except ValueError:
        return None

    payload = decode_access_token(token)
    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    return db.query(User).filter(User.id == int(user_id)).first()


def _serialize_comment(comment: FeedComment) -> dict:
    return {
        "id": comment.id,
        "content": comment.content,
        "created_at": comment.created_at,
        "author": {
            "id": comment.author.id,
            "name": comment.author.name,
            "email": comment.author.email,
            "phone": comment.author.phone,
            "role": comment.author.role.value if comment.author.role else "user"
        },
        "user_id": comment.author.id,
        "user_name": comment.author.name,
        "user_avatar": comment.author.profile_photo or "",
        "likes": 0
    }


def _serialize_feed(feed: Feed, current_user_id: Optional[int], include_comments: bool) -> dict:
    is_liked = False
    if current_user_id is not None:
        is_liked = any(like.user_id == current_user_id for like in feed.likes)

    response = {
        "id": feed.id,
        "title": feed.title,
        "content": feed.content,
        "image_url": feed.image_url,
        "likes_count": feed.likes_count,
        "likes": feed.likes_count,
        "shares": 0,
        "is_liked_by_current_user": is_liked,
        "author": {
            "id": feed.author.id,
            "name": feed.author.name,
            "email": feed.author.email,
            "phone": feed.author.phone,
            "role": feed.author.role.value if feed.author.role else "user"
        },
        "user_id": feed.author.id,
        "user_name": feed.author.name,
        "user_avatar": feed.author.profile_photo or "",
        "vehicle_type": "Thar",
        "created_at": feed.created_at,
        "updated_at": feed.updated_at,
    }

    response["comments"] = [_serialize_comment(comment) for comment in feed.comments] if include_comments else []
    return response


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
def list_feeds(
    skip: int = 0,
    limit: int = 10,
    q: Optional[str] = None,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Get list of community feeds with optional search."""
    if q is not None and q.strip():
        q = q.strip()
        if len(q) > 200 or not re.match(r"^[\w\s#@\-]+$", q):
            raise HTTPException(status_code=422, detail="Please enter a valid search term.")

    current_user = _optional_current_user(authorization, db)
    query = db.query(Feed).join(User, Feed.author_id == User.id)

    if q:
        search_value = f"%{q}%"
        query = query.filter(
            (Feed.title.ilike(search_value)) |
            (Feed.content.ilike(search_value)) |
            (User.name.ilike(search_value))
        )
        relevance = case(
            (Feed.title.ilike(search_value), 3),
            (Feed.content.ilike(search_value), 2),
            (User.name.ilike(search_value), 1),
            else_=0
        )
        query = query.order_by(relevance.desc(), Feed.created_at.desc())
    else:
        query = query.order_by(Feed.created_at.desc())

    feeds = query.offset(skip).limit(limit).all()
    current_user_id = current_user.id if current_user else None
    return [_serialize_feed(feed, current_user_id, include_comments=False) for feed in feeds]


@router.get("/{feed_id}", response_model=FeedResponse)
def get_feed(
    feed_id: int,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Get single feed with comments."""
    feed = db.query(Feed).filter(Feed.id == feed_id).first()
    if not feed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This post took an unmarked trail and disappeared!.")

    current_user = _optional_current_user(authorization, db)
    current_user_id = current_user.id if current_user else None
    return _serialize_feed(feed, current_user_id, include_comments=True)


@router.post("/{feed_id}/comments", response_model=FeedCommentResponse)
def add_comment(
    feed_id: int,
    comment_data: FeedCommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a comment to a feed post."""
    if not _has_active_club_membership(current_user.id, db):
        raise HTTPException(status_code=403, detail="You cannot interact with posts at this time.")

    feed = db.query(Feed).filter(Feed.id == feed_id).first()
    if not feed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This post took an unmarked trail and disappeared!.")
    
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


@router.post("/{feed_id}/like", response_model=FeedResponse)
def toggle_like(
    feed_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle like for a feed post (active club members only)."""
    if not _has_active_club_membership(current_user.id, db):
        raise HTTPException(status_code=403, detail="You cannot interact with posts at this time.")

    feed = db.query(Feed).filter(Feed.id == feed_id).first()
    if not feed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This post took an unmarked trail and disappeared!.")

    existing_like = db.query(FeedLike).filter(
        FeedLike.feed_id == feed_id,
        FeedLike.user_id == current_user.id
    ).first()

    if existing_like:
        db.delete(existing_like)
        feed.likes_count = max(0, (feed.likes_count or 0) - 1)
    else:
        new_like = FeedLike(feed_id=feed_id, user_id=current_user.id)
        db.add(new_like)
        feed.likes_count = (feed.likes_count or 0) + 1

    db.commit()

    refreshed_feed = db.query(Feed).filter(Feed.id == feed_id).first()
    return _serialize_feed(refreshed_feed, current_user.id, include_comments=True)
