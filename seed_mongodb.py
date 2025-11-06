"""
Seed MongoDB with data from local JSON file

Usage:
    python seed_mongodb.py

Environment Variables:
    MONGODB_URI - MongoDB connection string
"""

import json
import os
from pathlib import Path
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()


def seed_mongodb():
    """Upload pending reviews to MongoDB"""
    
    # Get MongoDB connection
    mongodb_uri = os.getenv('MONGODB_URI')
    if not mongodb_uri:
        print("❌ Error: MONGODB_URI not set in .env file")
        print("Add your MongoDB connection string to .env")
        return False
    
    # Load local data
    pending_file = Path("review_data/pending_reviews.json")
    
    if not pending_file.exists():
        print("❌ Error: review_data/pending_reviews.json not found")
        print("Run: python load_from_postgres.py first")
        return False
    
    with open(pending_file) as f:
        reviews = json.load(f)
    
    if not reviews:
        print("❌ No reviews found in pending_reviews.json")
        return False
    
    print(f"📦 Found {len(reviews)} reviews to upload")
    
    # Connect to MongoDB
    try:
        client = MongoClient(mongodb_uri)
        db = client['llm_reviews']
        
        # Clear existing pending reviews
        db['pending_reviews'].delete_many({})
        print("🗑️  Cleared existing pending reviews")
        
        # Insert new reviews
        result = db['pending_reviews'].insert_many(reviews)
        print(f"✅ Uploaded {len(result.inserted_ids)} reviews to MongoDB")
        
        # Show summary
        print(f"\n📊 Summary:")
        print(f"   Database: llm_reviews")
        print(f"   Collection: pending_reviews")
        print(f"   Documents: {db['pending_reviews'].count_documents({})}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to MongoDB: {e}")
        return False


if __name__ == '__main__':
    print("🚀 Seeding MongoDB from local data...\n")
    success = seed_mongodb()
    
    if success:
        print("\n✅ Done! Reviews are now in MongoDB.")
        print("   You can deploy to Vercel now.")
    else:
        print("\n❌ Failed to seed MongoDB")
        print("   Check your MONGODB_URI and try again")

