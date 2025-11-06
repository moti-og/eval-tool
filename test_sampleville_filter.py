#!/usr/bin/env python3
"""
Test script to verify Sampleville filter is working correctly

Run this before deploying to verify only Sampleville data is loaded.
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()


def test_sampleville_filter():
    """Test that the query only returns Sampleville data"""
    
    postgres_url = os.getenv('POSTGRES_URL')
    
    if not postgres_url:
        print("❌ POSTGRES_URL not found in .env file")
        print("Please set POSTGRES_URL in your .env file")
        return False
    
    try:
        print("Connecting to database...")
        conn = psycopg2.connect(postgres_url)
        cursor = conn.cursor()
        
        # Test the actual query with Sampleville filter
        test_query = """
        SELECT 
            a.id as ai_audit_id,
            p.title as user_prompt,
            COALESCE(o.name, 'Unknown Organization') as organization_name,
            g.code as government_code
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
        GROUP BY a.id, p.title, o.name, g.code
        LIMIT 10
        """
        
        print("✓ Connected successfully")
        print("\nTesting Sampleville filter...")
        print("-" * 60)
        
        cursor.execute(test_query)
        results = cursor.fetchall()
        
        if not results:
            print("⚠️  No results found with Sampleville filter")
            print("\nThis could mean:")
            print("  1. There's no AI audit data for Sampleville in your database")
            print("  2. The column name might be different (not 'code')")
            print("\nTrying to find the correct column name...")
            
            # Check government table structure
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'government' 
                AND table_schema = 'public'
                ORDER BY ordinal_position
            """)
            
            columns = [row[0] for row in cursor.fetchall()]
            print(f"\nGovernment table columns: {', '.join(columns)}")
            
            # Try to find a code-like column
            code_columns = [col for col in columns if 'code' in col.lower()]
            if code_columns:
                print(f"\nPossible code columns: {', '.join(code_columns)}")
                print("\nYou may need to update line 74 in load_from_postgres.py to use:")
                for col in code_columns:
                    print(f"  AND g.{col} = 'sampleville'")
            
            return False
        
        print(f"✓ Found {len(results)} Sampleville records")
        print("\nSample records:")
        print("-" * 60)
        
        all_sampleville = True
        for i, (aid, title, org, gov_code) in enumerate(results, 1):
            # Truncate long titles
            title_display = title[:50] + "..." if len(title) > 50 else title
            print(f"\n{i}. Project: {title_display}")
            print(f"   Organization: {org}")
            print(f"   Government Code: {gov_code}")
            
            if gov_code.lower() != 'sampleville':
                print(f"   ❌ WARNING: This is not Sampleville!")
                all_sampleville = False
        
        print("\n" + "=" * 60)
        
        if all_sampleville:
            print("✅ SUCCESS! Filter is working correctly.")
            print("All records are from Sampleville.")
            return True
        else:
            print("❌ FAIL! Some records are not from Sampleville.")
            return False
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


def check_government_codes():
    """Check what government codes exist in the database"""
    
    postgres_url = os.getenv('POSTGRES_URL')
    
    if not postgres_url:
        return
    
    try:
        conn = psycopg2.connect(postgres_url)
        cursor = conn.cursor()
        
        print("\n" + "=" * 60)
        print("Available Government Codes in Database")
        print("=" * 60)
        
        # Try to get government codes
        cursor.execute("""
            SELECT DISTINCT code, name
            FROM government
            WHERE code IS NOT NULL
            ORDER BY code
            LIMIT 20
        """)
        
        results = cursor.fetchall()
        
        if results:
            print("\nFound these government codes:")
            for code, name in results:
                marker = "✓" if code.lower() == 'sampleville' else " "
                print(f"  {marker} {code} - {name}")
            
            if not any(code.lower() == 'sampleville' for code, _ in results):
                print("\n⚠️  'sampleville' not found in the government codes")
                print("You may need to use a different government code in the filter")
        else:
            print("No government codes found or column name is different")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Could not check government codes: {e}")


if __name__ == '__main__':
    print("=" * 60)
    print("Sampleville Filter Test")
    print("=" * 60)
    print()
    
    # First check what government codes exist
    check_government_codes()
    
    # Then test the filter
    print()
    success = test_sampleville_filter()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ READY TO DEPLOY")
        print("The Sampleville filter is working correctly.")
    else:
        print("⚠️  NEEDS ATTENTION")
        print("Please review the output above and fix any issues before deploying.")
    print("=" * 60)

