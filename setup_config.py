"""
Setup script to configure MongoDB Data API credentials in index.html

Usage:
    python setup_config.py

This will:
1. Read your MongoDB Data API URL and key from .env
2. Update index.html with the correct values
3. Prepare for deployment
"""

import os
import re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def setup_config():
    """Configure index.html with MongoDB Data API credentials"""
    
    # Get values from environment
    api_url = os.getenv('MONGODB_DATA_API_URL')
    api_key = os.getenv('MONGODB_API_KEY')
    
    if not api_url or not api_key:
        print("❌ Error: Missing MongoDB Data API configuration")
        print("\nAdd to your .env file:")
        print("  MONGODB_DATA_API_URL=https://data.mongodb-api.com/app/YOUR-APP-ID/endpoint/data/v1")
        print("  MONGODB_API_KEY=your-api-key")
        print("\nHow to get these:")
        print("  1. Go to MongoDB Atlas → Data API")
        print("  2. Enable Data API")
        print("  3. Create an API Key")
        print("  4. Copy the endpoint URL and API key")
        return False
    
    # Read index.html
    index_file = Path("index.html")
    if not index_file.exists():
        print("❌ Error: index.html not found")
        return False
    
    content = index_file.read_text()
    
    # Replace placeholders
    content = content.replace('MONGODB_DATA_API_URL_PLACEHOLDER', api_url)
    content = content.replace('MONGODB_API_KEY_PLACEHOLDER', api_key)
    
    # Write back
    index_file.write_text(content)
    
    print("✅ index.html configured successfully!")
    print(f"\n📋 Configuration:")
    print(f"   API URL: {api_url}")
    print(f"   API Key: {api_key[:20]}...")
    print("\n✅ Ready to deploy!")
    print("   Run: vercel deploy")
    
    return True


if __name__ == '__main__':
    print("🔧 Configuring MongoDB Data API credentials...\n")
    success = setup_config()
    
    if not success:
        print("\n❌ Setup failed")
        print("   Fix the issues above and try again")
    else:
        print("\n🎉 All set! Deploy to Vercel:")
        print("   vercel deploy")

