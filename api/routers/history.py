"""Price history API endpoints"""
from fastapi import APIRouter, HTTPException, Depends, Query
from database.db_utils import DatabaseManager
from api.schemas import PriceHistoryResponse
from typing import List, Optional, Any
from datetime import datetime, timedelta, timezone

router = APIRouter()

def get_db():
    """Dependency to get database manager"""
    return DatabaseManager()

def safe_datetime_compare(obj_datetime: Any, compare_datetime: datetime) -> bool:
    """Safely compare datetime from SQLAlchemy object with regular datetime"""
    if obj_datetime is None:
        return False
    
    # If it's already a datetime, compare directly
    if isinstance(obj_datetime, datetime):
        return obj_datetime >= compare_datetime
    
    # If it has datetime-like attributes, try to use it
    if hasattr(obj_datetime, 'year') and hasattr(obj_datetime, 'month'):
        try:
            # Convert to datetime if needed
            if not isinstance(obj_datetime, datetime):
                return False
            return obj_datetime >= compare_datetime
        except (AttributeError, TypeError):
            return False
    
    return False

@router.get("/{platform}/{product_id}", response_model=List[PriceHistoryResponse])
def get_price_history(
    platform: str,
    product_id: str,
    days: Optional[int] = Query(30, ge=1, le=365, description="Number of days of history"),
    db: DatabaseManager = Depends(get_db)
):
    """Get price history for a specific product"""
    try:
        # Get price history from database
        price_history = db.get_price_history(platform, product_id)
        
        # Filter by days if specified
        if days:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            # Fix: Use safe comparison helper
            filtered_history = []
            for h in price_history:
                if safe_datetime_compare(h.scraped_at, cutoff_date):
                    filtered_history.append(h)
            price_history = filtered_history
        
        if not price_history:
            raise HTTPException(status_code=404, detail="No price history found for this product")
        
        # Convert to response models
        history_responses = []
        for history in price_history:
            history_dict = {
                'id': history.id,
                'platform': history.platform,
                'product_id': history.product_id,
                'price': history.price,
                'availability': history.availability,
                'scraped_at': history.scraped_at
            }
            history_responses.append(PriceHistoryResponse(**history_dict))
        
        return history_responses
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get price history: {str(e)}")

@router.get("/", response_model=List[PriceHistoryResponse])
def list_recent_price_changes(
    limit: int = Query(100, ge=1, le=500, description="Number of recent price changes"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    db: DatabaseManager = Depends(get_db)
):
    """List recent price changes across all products"""
    try:
        session = db.get_session()
        from database.models import PriceHistory
        query = session.query(PriceHistory)
        
        if platform:
            query = query.filter_by(platform=platform)
        
        price_changes = query.order_by(PriceHistory.scraped_at.desc()).limit(limit).all()
        session.close()
        
        history_responses = []
        for history in price_changes:
            history_dict = {
                'id': history.id,
                'platform': history.platform,
                'product_id': history.product_id,
                'price': history.price,
                'availability': history.availability,
                'scraped_at': history.scraped_at
            }
            history_responses.append(PriceHistoryResponse(**history_dict))
        
        return history_responses
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list price changes: {str(e)}")