"""Strategy rating and review system."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class StrategyReview:
    """Strategy review/rating."""
    review_id: str
    strategy_id: str
    user: str
    rating: float  # 1-5 stars
    comment: str
    created_at: datetime
    helpful_count: int = 0


class StrategyRating:
    """Strategy rating and review system."""
    
    def __init__(self):
        self.reviews: Dict[str, List[StrategyReview]] = {}
        
    def add_review(self, review: StrategyReview) -> bool:
        """Add a review for a strategy."""
        if review.strategy_id not in self.reviews:
            self.reviews[review.strategy_id] = []
            
        self.reviews[review.strategy_id].append(review)
        return True
        
    def get_reviews(self, strategy_id: str, limit: Optional[int] = None) -> List[StrategyReview]:
        """Get reviews for a strategy."""
        reviews = self.reviews.get(strategy_id, [])
        reviews.sort(key=lambda x: (x.helpful_count, x.created_at), reverse=True)
        
        if limit:
            reviews = reviews[:limit]
            
        return reviews
        
    def calculate_average_rating(self, strategy_id: str) -> float:
        """Calculate average rating for a strategy."""
        reviews = self.reviews.get(strategy_id, [])
        
        if not reviews:
            return 0.0
            
        return sum(r.rating for r in reviews) / len(reviews)
        
    def get_rating_distribution(self, strategy_id: str) -> Dict[int, int]:
        """Get rating distribution (1-5 stars)."""
        reviews = self.reviews.get(strategy_id, [])
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        
        for review in reviews:
            rating = int(review.rating)
            if 1 <= rating <= 5:
                distribution[rating] += 1
                
        return distribution

