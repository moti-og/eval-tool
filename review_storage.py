"""
Storage backends for human reviews

Supports: JSON, CSV, MongoDB
"""

import json
import csv
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from abc import ABC, abstractmethod


class ReviewStorage(ABC):
    """Base class for review storage"""
    
    @abstractmethod
    def save_review(self, review_data: Dict):
        """Save a review"""
        pass
    
    @abstractmethod
    def get_all_reviews(self) -> List[Dict]:
        """Get all reviews"""
        pass
    
    @abstractmethod
    def get_review_by_id(self, review_id: str) -> Optional[Dict]:
        """Get a specific review"""
        pass
    
    @abstractmethod
    def export_for_training(self, output_file: str):
        """Export reviews in format suitable for LLM fine-tuning"""
        pass


class JSONStorage(ReviewStorage):
    """Store reviews in JSON file"""
    
    def __init__(self, filepath: str = "review_data/reviews.json"):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(exist_ok=True)
        
        if not self.filepath.exists():
            self.filepath.write_text("[]")
    
    def save_review(self, review_data: Dict):
        reviews = self.get_all_reviews()
        reviews.append(review_data)
        
        with open(self.filepath, 'w') as f:
            json.dump(reviews, f, indent=2)
    
    def get_all_reviews(self) -> List[Dict]:
        with open(self.filepath) as f:
            return json.load(f)
    
    def get_review_by_id(self, review_id: str) -> Optional[Dict]:
        reviews = self.get_all_reviews()
        return next((r for r in reviews if r.get('review_id') == review_id), None)
    
    def export_for_training(self, output_file: str):
        """Export as JSONL for training"""
        reviews = self.get_all_reviews()
        
        with open(output_file, 'w') as f:
            for review in reviews:
                # Format for training: only include highly-rated responses
                if review.get('rating', 0) >= 4:
                    training_example = {
                        "prompt": review.get('prompt'),
                        "context": review.get('context'),
                        "response": review.get('response'),
                        "rating": review.get('rating'),
                        "metadata": {
                            "feature": review.get('feature'),
                            "reviewer": review.get('reviewer'),
                            "timestamp": review.get('timestamp')
                        }
                    }
                    f.write(json.dumps(training_example) + '\n')


class CSVStorage(ReviewStorage):
    """Store reviews in CSV file"""
    
    def __init__(self, filepath: str = "review_data/reviews.csv"):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(exist_ok=True)
        
        if not self.filepath.exists():
            # Create with headers
            with open(self.filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'review_id', 'timestamp', 'reviewer', 'prompt', 'context',
                    'response', 'expected_output', 'model', 'feature', 'rating',
                    'accurate', 'relevant', 'complete', 'well_formatted',
                    'has_issues', 'notes', 'tags'
                ])
    
    def save_review(self, review_data: Dict):
        with open(self.filepath, 'a', newline='') as f:
            writer = csv.writer(f)
            
            criteria = review_data.get('criteria', {})
            issues = review_data.get('issues', {})
            has_issues = any(issues.values())
            
            writer.writerow([
                review_data.get('review_id'),
                review_data.get('timestamp'),
                review_data.get('reviewer'),
                review_data.get('prompt'),
                review_data.get('context'),
                review_data.get('response'),
                review_data.get('expected_output'),
                review_data.get('model'),
                review_data.get('feature'),
                review_data.get('rating'),
                criteria.get('accurate', False),
                criteria.get('relevant', False),
                criteria.get('complete', False),
                criteria.get('well_formatted', False),
                has_issues,
                review_data.get('notes'),
                ','.join(review_data.get('tags', []))
            ])
    
    def get_all_reviews(self) -> List[Dict]:
        reviews = []
        
        with open(self.filepath, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert string booleans back
                row['accurate'] = row['accurate'].lower() == 'true'
                row['relevant'] = row['relevant'].lower() == 'true'
                row['complete'] = row['complete'].lower() == 'true'
                row['well_formatted'] = row['well_formatted'].lower() == 'true'
                row['has_issues'] = row['has_issues'].lower() == 'true'
                row['tags'] = row['tags'].split(',') if row['tags'] else []
                
                reviews.append(row)
        
        return reviews
    
    def get_review_by_id(self, review_id: str) -> Optional[Dict]:
        reviews = self.get_all_reviews()
        return next((r for r in reviews if r.get('review_id') == review_id), None)
    
    def export_for_training(self, output_file: str):
        """Export high-quality responses as JSONL"""
        reviews = self.get_all_reviews()
        
        with open(output_file, 'w') as f:
            for review in reviews:
                if int(review.get('rating', 0)) >= 4:
                    training_example = {
                        "prompt": review.get('prompt'),
                        "context": review.get('context'),
                        "response": review.get('response'),
                        "rating": review.get('rating')
                    }
                    f.write(json.dumps(training_example) + '\n')


class MongoDBStorage(ReviewStorage):
    """Store reviews in MongoDB"""
    
    def __init__(self, connection_string: str, db_name: str = "llm_reviews", collection_name: str = "reviews"):
        try:
            from pymongo import MongoClient
        except ImportError:
            raise ImportError("pymongo not installed. Run: pip install pymongo")
        
        self.client = MongoClient(connection_string)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        
        # Create indexes
        self.collection.create_index("review_id", unique=True)
        self.collection.create_index("timestamp")
        self.collection.create_index("rating")
        self.collection.create_index("feature")
    
    def save_review(self, review_data: Dict):
        self.collection.insert_one(review_data)
    
    def get_all_reviews(self) -> List[Dict]:
        return list(self.collection.find({}, {'_id': 0}))
    
    def get_review_by_id(self, review_id: str) -> Optional[Dict]:
        return self.collection.find_one({'review_id': review_id}, {'_id': 0})
    
    def export_for_training(self, output_file: str):
        """Export high-quality responses as JSONL"""
        reviews = self.collection.find({'rating': {'$gte': 4}}, {'_id': 0})
        
        with open(output_file, 'w') as f:
            for review in reviews:
                training_example = {
                    "prompt": review.get('prompt'),
                    "context": review.get('context'),
                    "response": review.get('response'),
                    "rating": review.get('rating'),
                    "metadata": {
                        "feature": review.get('feature'),
                        "reviewer": review.get('reviewer'),
                        "timestamp": review.get('timestamp')
                    }
                }
                f.write(json.dumps(training_example) + '\n')
    
    def get_stats(self) -> Dict:
        """Get review statistics"""
        pipeline = [
            {
                '$group': {
                    '_id': None,
                    'total_reviews': {'$sum': 1},
                    'avg_rating': {'$avg': '$rating'},
                    'min_rating': {'$min': '$rating'},
                    'max_rating': {'$max': '$rating'}
                }
            }
        ]
        
        result = list(self.collection.aggregate(pipeline))
        return result[0] if result else {}

