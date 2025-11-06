"""
Smart Storage - Automatically uses MongoDB in production, JSON locally

Environment detection:
- Local dev: JSON file (fast, no setup)
- Production (Vercel/etc): MongoDB (persistent)
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


def is_production():
    """Detect if running in production environment"""
    return bool(os.getenv('VERCEL') or os.getenv('MONGODB_URI'))


def get_storage():
    """Get appropriate storage based on environment"""
    if is_production():
        # Production: Use MongoDB
        from review_storage import MongoDBStorage
        
        mongodb_uri = os.getenv('MONGODB_URI')
        if not mongodb_uri:
            raise ValueError("MONGODB_URI not set in production environment")
        
        print("📦 Using MongoDB storage (production mode)")
        return MongoDBStorage(
            connection_string=mongodb_uri,
            db_name=os.getenv('MONGODB_DB_NAME', 'llm_reviews'),
            collection_name=os.getenv('MONGODB_COLLECTION', 'reviews')
        )
    else:
        # Local dev: Use JSON
        from review_storage import JSONStorage
        
        print("📦 Using JSON storage (local dev mode)")
        return JSONStorage("review_data/reviews.json")


class SmartStorage:
    """
    Wrapper that delegates to the appropriate storage backend
    Adds some convenience methods for both
    """
    
    def __init__(self):
        self.backend = get_storage()
        self.is_mongo = is_production()
    
    def save_review(self, review_data: Dict):
        """Save a review"""
        return self.backend.save_review(review_data)
    
    def get_all_reviews(self) -> List[Dict]:
        """Get all reviews"""
        return self.backend.get_all_reviews()
    
    def get_review_by_id(self, review_id: str) -> Optional[Dict]:
        """Get a specific review"""
        return self.backend.get_review_by_id(review_id)
    
    def export_for_training(self, output_file: str):
        """Export reviews in format suitable for LLM fine-tuning"""
        return self.backend.export_for_training(output_file)
    
    def get_stats(self) -> Dict:
        """Get review statistics"""
        reviews = self.get_all_reviews()
        
        if not reviews:
            return {"total": 0}
        
        acceptable_count = sum(1 for r in reviews if r.get('acceptable'))
        
        # Get unique values
        organizations = set()
        reviewers = set()
        features = set()
        
        for r in reviews:
            if r.get('organization_name'):
                organizations.add(r.get('organization_name'))
            if r.get('reviewer'):
                reviewers.add(r.get('reviewer'))
            if r.get('feature'):
                features.add(r.get('feature'))
        
        return {
            "total_reviews": len(reviews),
            "acceptable": acceptable_count,
            "not_acceptable": len(reviews) - acceptable_count,
            "acceptance_rate": (acceptable_count / len(reviews) * 100) if reviews else 0,
            "organizations": len(organizations),
            "reviewers": len(reviewers),
            "features": len(features),
            "storage_type": "MongoDB" if self.is_mongo else "JSON"
        }
    
    def get_reviews_by_organization(self, org_name: str) -> List[Dict]:
        """Get all reviews for a specific organization"""
        reviews = self.get_all_reviews()
        return [r for r in reviews if r.get('organization_name') == org_name]
    
    def get_recent_reviews(self, limit: int = 20) -> List[Dict]:
        """Get most recent reviews"""
        reviews = self.get_all_reviews()
        # Sort by timestamp descending
        sorted_reviews = sorted(
            reviews, 
            key=lambda x: x.get('timestamp', ''), 
            reverse=True
        )
        return sorted_reviews[:limit]

