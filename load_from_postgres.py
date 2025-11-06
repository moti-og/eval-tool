"""
Load LLM conversations from PostgreSQL database

This script pulls LLM interactions from your OpenGov Postgres database
and loads them into the review queue.
"""

import psycopg2
import json
from pathlib import Path
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()


class PostgresLoader:
    """Load LLM data from Postgres"""
    
    def __init__(self, connection_string=None):
        """
        Initialize with Postgres connection
        
        Args:
            connection_string: PostgreSQL connection string
                              Format: postgresql://user:pass@host:port/dbname
        """
        self.connection_string = connection_string or os.getenv('POSTGRES_URL')
        if not self.connection_string:
            raise ValueError("POSTGRES_URL not found. Set it in .env file")
    
    def connect(self):
        """Create database connection"""
        return psycopg2.connect(self.connection_string)
    
    def load_conversations(self, query=None, limit=100):
        """
        Load LLM conversations from database
        
        Args:
            query: Custom SQL query (optional)
            limit: Maximum number of records to load
            
        Returns:
            List of conversation records
        """
        if not query:
            # OpenGov-specific query: Load likely AI-generated criteria
            # (criteria created within 15 minutes after AI prompt)
            query = f"""
            SELECT 
                a.id as ai_audit_id,
                p.title as user_prompt,
                string_agg(c.description, '\n\n---CRITERIA---\n\n' ORDER BY c.created_at) as llm_response,
                'User saved ' || COUNT(c.id) || ' criteria within ' || 
                    ROUND(AVG(EXTRACT(EPOCH FROM (c.created_at::timestamp - a.created_at::timestamp))/60)) || ' min' as context_data,
                'unknown' as model_name,
                'procurement_criteria_generation' as feature_name,
                a.user_id,
                a.created_at,
                COALESCE(p.contact_first_name || ' ' || p.contact_last_name, 'Unknown') as agency_user,
                COALESCE(o.name, 'Unknown Organization') as organization_name
            FROM ai_audit a
            JOIN project p ON a.project_id = p.id
            JOIN government g ON p.government_id = g.id
            LEFT JOIN organization o ON g.organization_id = o.id
            JOIN project_section ps ON p.id = ps.project_id
            JOIN criteria c ON ps.id = c.project_section_id
            WHERE c.created_at::timestamp BETWEEN a.created_at::timestamp 
                  AND (a.created_at::timestamp + INTERVAL '15 minutes')
              AND c.description IS NOT NULL
              AND LENGTH(c.description) > 100
              AND g.code = 'sampleville'
            GROUP BY a.id, p.title, a.user_id, a.created_at, p.contact_first_name, p.contact_last_name, o.name
            HAVING COUNT(c.id) > 0
            ORDER BY a.created_at DESC
            LIMIT {limit}
            """
        
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                record = dict(zip(columns, row))
                results.append(record)
            
            return results
        
        finally:
            cursor.close()
            conn.close()
    
    def format_for_review(self, records):
        """
        Convert database records to review format
        
        Args:
            records: List of database records
            
        Returns:
            List of formatted review items
        """
        review_items = []
        
        for record in records:
            review_item = {
                "id": str(record.get('ai_audit_id', '')),
                "timestamp": record.get('created_at', datetime.now()).isoformat(),
                "prompt": record.get('user_prompt', ''),
                "response": record.get('llm_response', ''),
                "context": record.get('context_data', ''),
                "model": record.get('model_name', 'unknown'),
                "feature": record.get('feature_name', 'unknown'),
                "user_id": record.get('user_id', ''),
                "agency_user": record.get('agency_user', 'Unknown'),
                "organization_name": record.get('organization_name', 'Unknown Organization'),
                "expected_output": None,
                "metadata": {
                    "source": "postgres",
                    "original_id": record.get('ai_audit_id')
                }
            }
            review_items.append(review_item)
        
        return review_items
    
    def save_to_pending_reviews(self, review_items, replace=True):
        """
        Save items to pending reviews file
        
        Args:
            review_items: List of formatted review items
            replace: If True, replace existing data. If False, append and avoid duplicates.
                     Default True for clean deployments.
        """
        pending_file = Path("review_data/pending_reviews.json")
        backup_file = Path("review_data/master_reviews_backup.json")
        pending_file.parent.mkdir(exist_ok=True)
        
        if replace:
            # REPLACE mode: Wipe existing data and use only new items
            # This is the default for clean deployments
            with open(pending_file, 'w') as f:
                json.dump(review_items, f, indent=2)
            
            # Also create backup for reload functionality
            with open(backup_file, 'w') as f:
                json.dump(review_items, f, indent=2)
            
            print(f"✓ Replaced pending reviews with {len(review_items)} items")
            print(f"✓ Created backup at {backup_file}")
            print(f"  Total pending: {len(review_items)}")
        else:
            # APPEND mode: Keep existing and add new (avoiding duplicates)
            if pending_file.exists():
                with open(pending_file) as f:
                    existing = json.load(f)
            else:
                existing = []
            
            # Add new items (avoiding duplicates)
            existing_ids = {item.get('id') for item in existing}
            new_items = [item for item in review_items if item.get('id') not in existing_ids]
            
            existing.extend(new_items)
            
            # Save back
            with open(pending_file, 'w') as f:
                json.dump(existing, f, indent=2)
            
            print(f"✓ Added {len(new_items)} new items to review queue")
            print(f"  Total pending: {len(existing)}")


def main():
    """
    Main function to load data from Postgres
    
    Usage:
        python load_from_postgres.py
    
    IMPORTANT FOR DEPLOYMENT:
    - This script WIPES existing pending_reviews.json and replaces it with fresh data
    - Only loads 10 items from Sampleville (g.code = 'sampleville')
    - After running, pending_reviews.json will have exactly 10 items
    """
    
    # Initialize loader
    loader = PostgresLoader()
    
    print("=" * 60)
    print("Loading Sampleville data for review")
    print("=" * 60)
    print()
    
    # Option 1: Use default query (limited to 10 for Sampleville testing)
    records = loader.load_conversations(limit=10)
    
    # Option 2: Use custom query
    # custom_query = '''
    #     SELECT * FROM your_table
    #     WHERE some_condition = true
    #     LIMIT 50
    # '''
    # records = loader.load_conversations(query=custom_query)
    
    print(f"✓ Loaded {len(records)} records from database")
    
    # Format for review
    review_items = loader.format_for_review(records)
    
    # Save to pending reviews (REPLACES existing data by default)
    # This ensures a clean slate with only Sampleville data for deployment
    loader.save_to_pending_reviews(review_items, replace=True)
    
    # To append instead of replace, use: loader.save_to_pending_reviews(review_items, replace=False)
    
    print()
    print("=" * 60)
    print("✅ DEPLOYMENT READY")
    print("=" * 60)
    print(f"Loaded exactly {len(review_items)} Sampleville items")
    print("Old data has been WIPED and replaced")
    print()
    print("Next step: Run 'streamlit run human_review_app.py --server.port 8069'")
    print("=" * 60)


if __name__ == '__main__':
    main()

