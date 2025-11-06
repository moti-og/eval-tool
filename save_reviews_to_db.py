"""
Save human reviews back to PostgreSQL database

This script takes the reviews from JSON and saves them to your Postgres database
"""

import psycopg2
import json
from pathlib import Path
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()


class ReviewDatabaseSaver:
    """Save reviews to Postgres database"""
    
    def __init__(self, connection_string=None):
        self.connection_string = connection_string or os.getenv('POSTGRES_URL')
        if not self.connection_string:
            raise ValueError("POSTGRES_URL not found. Set it in .env file")
    
    def connect(self):
        """Create database connection"""
        return psycopg2.connect(self.connection_string)
    
    def create_reviews_table(self):
        """
        Create the human_reviews table if it doesn't exist
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS llm_human_reviews (
                    id SERIAL PRIMARY KEY,
                    review_id VARCHAR(255) UNIQUE NOT NULL,
                    original_conversation_id VARCHAR(255),
                    timestamp TIMESTAMP NOT NULL,
                    reviewer VARCHAR(255),
                    
                    -- Original LLM data
                    prompt TEXT,
                    context TEXT,
                    response TEXT,
                    expected_output TEXT,
                    model VARCHAR(100),
                    feature VARCHAR(100),
                    
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
            """)
            
            conn.commit()
            print("✓ Reviews table created/verified")
        
        finally:
            cursor.close()
            conn.close()
    
    def save_review(self, review_data):
        """
        Save a single review to database
        
        Args:
            review_data: Review dictionary
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO llm_human_reviews (
                    review_id, timestamp, reviewer,
                    prompt, context, response, expected_output,
                    model, feature,
                    acceptable, score_choice, notes, tags
                ) VALUES (
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s,
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
                review_data.get('acceptable'),
                review_data.get('score_choice'),
                review_data.get('notes'),
                review_data.get('tags', [])
            ))
            
            conn.commit()
        
        finally:
            cursor.close()
            conn.close()
    
    def sync_from_json(self):
        """
        Load all reviews from JSON and save to database
        """
        reviews_file = Path("review_data/reviews.json")
        
        if not reviews_file.exists():
            print("No reviews file found")
            return
        
        with open(reviews_file) as f:
            reviews = json.load(f)
        
        print(f"Syncing {len(reviews)} reviews to database...")
        
        for i, review in enumerate(reviews, 1):
            try:
                self.save_review(review)
                if i % 10 == 0:
                    print(f"  Synced {i}/{len(reviews)}")
            except Exception as e:
                print(f"  Error syncing review {review.get('review_id')}: {e}")
        
        print(f"✓ Sync complete: {len(reviews)} reviews")


def main():
    """
    Main function to save reviews to Postgres
    
    Usage:
        python save_reviews_to_db.py
    """
    
    saver = ReviewDatabaseSaver()
    
    # Create table if it doesn't exist
    print("Setting up database table...")
    saver.create_reviews_table()
    
    # Sync reviews from JSON to database
    print("\nSyncing reviews to database...")
    saver.sync_from_json()
    
    print("\n✓ Done!")


if __name__ == '__main__':
    main()

