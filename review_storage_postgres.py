"""
Dual storage: JSON (for speed) + PostgreSQL (for permanence)

Automatically saves reviews to both JSON file and Postgres database
"""

import json
import psycopg2
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()


class DualStorage:
    """Store reviews in both JSON (fast) and Postgres (permanent)"""
    
    def __init__(self, json_filepath: str = "review_data/reviews.json", 
                 postgres_url: str = None):
        # JSON setup
        self.json_filepath = Path(json_filepath)
        self.json_filepath.parent.mkdir(exist_ok=True)
        
        if not self.json_filepath.exists():
            self.json_filepath.write_text("[]")
        
        # Postgres setup
        self.postgres_url = postgres_url or os.getenv('POSTGRES_URL')
        self.use_postgres = bool(self.postgres_url)
        
        if self.use_postgres:
            self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Create the reviews table if it doesn't exist"""
        try:
            conn = psycopg2.connect(self.postgres_url)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS llm_human_reviews (
                    id SERIAL PRIMARY KEY,
                    review_id VARCHAR(255) UNIQUE NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    reviewer VARCHAR(255),
                    
                    -- Original LLM data
                    prompt TEXT,
                    context TEXT,
                    response TEXT,
                    expected_output TEXT,
                    model VARCHAR(100),
                    feature VARCHAR(100),
                    user_id VARCHAR(255),
                    agency_user VARCHAR(255),
                    organization_name VARCHAR(255),
                    
                    -- Review data
                    acceptable BOOLEAN,
                    score_choice VARCHAR(50),
                    notes TEXT,
                    tags TEXT[],
                    
                    -- Metadata
                    created_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_review_timestamp ON llm_human_reviews(timestamp);
                CREATE INDEX IF NOT EXISTS idx_acceptable ON llm_human_reviews(acceptable);
                CREATE INDEX IF NOT EXISTS idx_feature ON llm_human_reviews(feature);
                CREATE INDEX IF NOT EXISTS idx_organization ON llm_human_reviews(organization_name);
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            print("✓ PostgreSQL table ready")
        except Exception as e:
            print(f"⚠ PostgreSQL not available: {e}")
            self.use_postgres = False
    
    def save_review(self, review_data: Dict):
        """Save review to both JSON and Postgres"""
        # Save to JSON (always)
        reviews = self._load_json()
        reviews.append(review_data)
        
        with open(self.json_filepath, 'w') as f:
            json.dump(reviews, f, indent=2)
        
        # Save to Postgres (if available)
        if self.use_postgres:
            try:
                self._save_to_postgres(review_data)
            except Exception as e:
                print(f"⚠ Failed to save to Postgres: {e}")
    
    def _save_to_postgres(self, review_data: Dict):
        """Save a single review to Postgres"""
        conn = psycopg2.connect(self.postgres_url)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO llm_human_reviews (
                    review_id, timestamp, reviewer,
                    prompt, context, response, expected_output,
                    model, feature, user_id, agency_user, organization_name,
                    acceptable, score_choice, notes, tags
                ) VALUES (
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
                ON CONFLICT (review_id) DO UPDATE SET
                    acceptable = EXCLUDED.acceptable,
                    score_choice = EXCLUDED.score_choice,
                    notes = EXCLUDED.notes,
                    tags = EXCLUDED.tags
            """, (
                review_data.get('review_id'),
                review_data.get('timestamp'),
                review_data.get('reviewer'),
                review_data.get('prompt'),
                review_data.get('context'),
                review_data.get('response'),
                review_data.get('expected_output'),
                review_data.get('model'),
                review_data.get('feature'),
                review_data.get('user_id'),
                review_data.get('agency_user'),
                review_data.get('organization_name'),
                review_data.get('acceptable'),
                review_data.get('score_choice'),
                review_data.get('notes'),
                review_data.get('tags', [])
            ))
            
            conn.commit()
        finally:
            cursor.close()
            conn.close()
    
    def _load_json(self) -> List[Dict]:
        """Load reviews from JSON"""
        with open(self.json_filepath) as f:
            return json.load(f)
    
    def get_all_reviews(self) -> List[Dict]:
        """Get all reviews from JSON"""
        return self._load_json()
    
    def get_review_by_id(self, review_id: str) -> Optional[Dict]:
        """Get a specific review"""
        reviews = self._load_json()
        return next((r for r in reviews if r.get('review_id') == review_id), None)
    
    def export_for_training(self, output_file: str):
        """Export acceptable reviews as JSONL for LLM fine-tuning"""
        reviews = self._load_json()
        
        with open(output_file, 'w') as f:
            for review in reviews:
                # Only export acceptable responses
                if review.get('acceptable'):
                    training_example = {
                        "messages": [
                            {
                                "role": "user",
                                "content": review.get('prompt')
                            },
                            {
                                "role": "assistant", 
                                "content": review.get('response')
                            }
                        ],
                        "metadata": {
                            "feature": review.get('feature'),
                            "organization": review.get('organization_name'),
                            "reviewer": review.get('reviewer'),
                            "timestamp": review.get('timestamp'),
                            "notes": review.get('notes')
                        }
                    }
                    f.write(json.dumps(training_example) + '\n')
        
        print(f"✓ Exported training data to {output_file}")
    
    def get_stats(self) -> Dict:
        """Get review statistics"""
        reviews = self._load_json()
        
        if not reviews:
            return {"total": 0}
        
        acceptable_count = sum(1 for r in reviews if r.get('acceptable'))
        
        return {
            "total_reviews": len(reviews),
            "acceptable": acceptable_count,
            "not_acceptable": len(reviews) - acceptable_count,
            "acceptance_rate": (acceptable_count / len(reviews) * 100) if reviews else 0,
            "organizations": len(set(r.get('organization_name') for r in reviews if r.get('organization_name'))),
            "reviewers": len(set(r.get('reviewer') for r in reviews if r.get('reviewer')))
        }

