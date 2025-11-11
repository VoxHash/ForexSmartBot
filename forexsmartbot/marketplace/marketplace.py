"""Strategy marketplace for sharing and discovering strategies."""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class StrategyListing:
    """Strategy listing in marketplace."""
    strategy_id: str
    name: str
    description: str
    author: str
    version: str
    category: str
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    download_count: int = 0
    rating: float = 0.0
    rating_count: int = 0
    file_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StrategyListing':
        """Create from dictionary."""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


class StrategyMarketplace:
    """Marketplace for strategy sharing."""
    
    def __init__(self, storage_path: str = "marketplace"):
        """
        Initialize marketplace.
        
        Args:
            storage_path: Path to store marketplace data
        """
        self.storage_path = storage_path
        self.listings_file = os.path.join(storage_path, "listings.json")
        self.listings: Dict[str, StrategyListing] = {}
        
        # Create storage directory if it doesn't exist
        os.makedirs(storage_path, exist_ok=True)
        
        # Load existing listings
        self._load_listings()
        
    def _load_listings(self) -> None:
        """Load listings from storage."""
        if os.path.exists(self.listings_file):
            try:
                with open(self.listings_file, 'r') as f:
                    data = json.load(f)
                    self.listings = {
                        listing_id: StrategyListing.from_dict(listing_data)
                        for listing_id, listing_data in data.items()
                    }
            except Exception as e:
                print(f"Error loading marketplace listings: {e}")
                self.listings = {}
        else:
            self.listings = {}
            
    def _save_listings(self) -> None:
        """Save listings to storage."""
        try:
            data = {
                listing_id: listing.to_dict()
                for listing_id, listing in self.listings.items()
            }
            with open(self.listings_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving marketplace listings: {e}")
            
    def add_listing(self, listing: StrategyListing) -> bool:
        """Add a strategy listing."""
        self.listings[listing.strategy_id] = listing
        self._save_listings()
        return True
        
    def remove_listing(self, strategy_id: str) -> bool:
        """Remove a strategy listing."""
        if strategy_id in self.listings:
            del self.listings[strategy_id]
            self._save_listings()
            return True
        return False
        
    def get_listing(self, strategy_id: str) -> Optional[StrategyListing]:
        """Get a strategy listing by ID."""
        return self.listings.get(strategy_id)
        
    def search_listings(self, query: Optional[str] = None, 
                       category: Optional[str] = None,
                       tags: Optional[List[str]] = None,
                       min_rating: float = 0.0) -> List[StrategyListing]:
        """Search for strategy listings."""
        results = list(self.listings.values())
        
        # Filter by query
        if query:
            query_lower = query.lower()
            results = [
                listing for listing in results
                if query_lower in listing.name.lower() or 
                   query_lower in listing.description.lower()
            ]
            
        # Filter by category
        if category:
            results = [listing for listing in results if listing.category == category]
            
        # Filter by tags
        if tags:
            results = [
                listing for listing in results
                if any(tag in listing.tags for tag in tags)
            ]
            
        # Filter by rating
        results = [listing for listing in results if listing.rating >= min_rating]
        
        # Sort by rating and download count
        results.sort(key=lambda x: (x.rating, x.download_count), reverse=True)
        
        return results
        
    def update_rating(self, strategy_id: str, rating: float) -> bool:
        """Update strategy rating."""
        if strategy_id not in self.listings:
            return False
            
        listing = self.listings[strategy_id]
        
        # Update rating (simple average)
        total_rating = listing.rating * listing.rating_count
        listing.rating_count += 1
        listing.rating = (total_rating + rating) / listing.rating_count
        
        self._save_listings()
        return True
        
    def increment_download(self, strategy_id: str) -> bool:
        """Increment download count."""
        if strategy_id not in self.listings:
            return False
            
        self.listings[strategy_id].download_count += 1
        self._save_listings()
        return True
        
    def get_popular_strategies(self, limit: int = 10) -> List[StrategyListing]:
        """Get most popular strategies."""
        listings = list(self.listings.values())
        listings.sort(key=lambda x: (x.rating * x.rating_count + x.download_count), reverse=True)
        return listings[:limit]
        
    def get_recent_strategies(self, limit: int = 10) -> List[StrategyListing]:
        """Get most recently added strategies."""
        listings = list(self.listings.values())
        listings.sort(key=lambda x: x.created_at, reverse=True)
        return listings[:limit]

