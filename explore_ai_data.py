"""
Explore database to find AI response data

This script investigates:
1. ai_audit table structure
2. Tables that reference ai_audit (foreign keys)
3. Long text/HTML columns that might contain AI responses
4. Related tables that might have the actual AI output
"""

import psycopg2
import os

# Connection from Teleport
POSTGRES_URL = "postgresql://usr_teleport_reader@localhost:51329/procurement_prod"

def explore_ai_audit():
    """Look at ai_audit table in detail"""
    conn = psycopg2.connect(POSTGRES_URL)
    cursor = conn.cursor()
    
    print("="*70)
    print("STEP 1: Examining ai_audit table")
    print("="*70)
    
    # Get columns
    cursor.execute("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns 
        WHERE table_name = 'ai_audit'
        ORDER BY ordinal_position
    """)
    
    print("\nColumns in ai_audit:")
    print("-"*70)
    for col, dtype, max_len in cursor.fetchall():
        len_str = f"({max_len})" if max_len else ""
        print(f"  {col:<30} {dtype}{len_str}")
    
    # Get sample data
    cursor.execute("SELECT * FROM ai_audit LIMIT 3")
    rows = cursor.fetchall()
    cols = [desc[0] for desc in cursor.description]
    
    print("\nSample data from ai_audit:")
    print("-"*70)
    for i, row in enumerate(rows, 1):
        print(f"\nRow {i}:")
        for col, val in zip(cols, row):
            val_str = str(val)[:200] if val else "NULL"
            print(f"  {col}: {val_str}")
    
    # Get row count
    cursor.execute("SELECT COUNT(*) FROM ai_audit")
    count = cursor.fetchone()[0]
    print(f"\nTotal rows in ai_audit: {count:,}")
    
    cursor.close()
    conn.close()


def find_foreign_keys_to_ai_audit():
    """Find tables that reference ai_audit"""
    conn = psycopg2.connect(POSTGRES_URL)
    cursor = conn.cursor()
    
    print("\n" + "="*70)
    print("STEP 2: Finding tables that reference ai_audit")
    print("="*70)
    
    cursor.execute("""
        SELECT
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND ccu.table_name = 'ai_audit'
    """)
    
    related_tables = cursor.fetchall()
    
    if related_tables:
        print("\nTables with foreign keys to ai_audit:")
        for table, col, foreign_table, foreign_col in related_tables:
            print(f"  {table}.{col} → {foreign_table}.{foreign_col}")
    else:
        print("\n⚠️  No foreign keys found pointing to ai_audit")
        print("   The response might be in the same table or linked by ID matching")
    
    cursor.close()
    conn.close()
    
    return [t[0] for t in related_tables]


def find_tables_with_ai_columns():
    """Find all tables with columns mentioning 'ai' or having long text"""
    conn = psycopg2.connect(POSTGRES_URL)
    cursor = conn.cursor()
    
    print("\n" + "="*70)
    print("STEP 3: Finding tables with AI-related or long text columns")
    print("="*70)
    
    cursor.execute("""
        SELECT DISTINCT
            table_name,
            column_name,
            data_type,
            character_maximum_length
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND (
            column_name LIKE '%ai%'
            OR column_name LIKE '%response%'
            OR column_name LIKE '%output%'
            OR column_name LIKE '%result%'
            OR column_name LIKE '%content%'
            OR column_name LIKE '%html%'
            OR column_name LIKE '%text%'
            OR data_type IN ('text', 'json', 'jsonb')
          )
        ORDER BY table_name, column_name
    """)
    
    results = cursor.fetchall()
    
    print("\nPotentially interesting columns:")
    print("-"*70)
    current_table = None
    for table, col, dtype, max_len in results:
        if table != current_table:
            print(f"\n📋 {table}:")
            current_table = table
        len_str = f" ({max_len})" if max_len else ""
        print(f"   {col:<40} {dtype}{len_str}")
    
    cursor.close()
    conn.close()


def explore_project_tables():
    """Look at project-related tables"""
    conn = psycopg2.connect(POSTGRES_URL)
    cursor = conn.cursor()
    
    print("\n" + "="*70)
    print("STEP 4: Exploring project-related tables")
    print("="*70)
    
    # Find project tables
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name LIKE '%project%'
        ORDER BY table_name
    """)
    
    project_tables = [t[0] for t in cursor.fetchall()]
    
    if project_tables:
        print(f"\nFound {len(project_tables)} project-related tables:")
        for table in project_tables:
            print(f"  - {table}")
            
            # Show columns for each
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, (table,))
            
            cols = cursor.fetchall()
            for col, dtype in cols:
                if any(kw in col.lower() for kw in ['ai', 'response', 'content', 'text', 'html']):
                    print(f"      → {col} ({dtype})")
    else:
        print("\n⚠️  No project-related tables found")
    
    cursor.close()
    conn.close()


def sample_long_text_columns():
    """Sample data from tables with long text that might be AI responses"""
    conn = psycopg2.connect(POSTGRES_URL)
    cursor = conn.cursor()
    
    print("\n" + "="*70)
    print("STEP 5: Sampling long text columns for AI content")
    print("="*70)
    
    # Get tables with text columns
    cursor.execute("""
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND data_type IN ('text', 'character varying')
          AND (
            column_name LIKE '%response%'
            OR column_name LIKE '%content%'
            OR column_name LIKE '%html%'
            OR column_name LIKE '%body%'
            OR column_name LIKE '%text%'
          )
        LIMIT 10
    """)
    
    text_columns = cursor.fetchall()
    
    for table, column in text_columns:
        try:
            cursor.execute(f"""
                SELECT {column}
                FROM {table}
                WHERE {column} IS NOT NULL
                  AND LENGTH({column}) > 100
                LIMIT 2
            """)
            
            samples = cursor.fetchall()
            
            if samples:
                print(f"\n📝 {table}.{column}:")
                for i, (text,) in enumerate(samples, 1):
                    text_preview = str(text)[:300]
                    print(f"   Sample {i}: {text_preview}...")
                    
                    # Check if it looks like AI content
                    if any(indicator in text_preview.lower() for indicator in 
                           ['based on', 'according to', 'analysis', 'recommend', 
                            'suggest', 'data shows', 'gpt', 'ai', 'llm']):
                        print(f"   ⭐ Might be AI content!")
        except Exception as e:
            pass
    
    cursor.close()
    conn.close()


def find_ai_audit_id_usage():
    """Find where ai_audit IDs are used in other tables"""
    conn = psycopg2.connect(POSTGRES_URL)
    cursor = conn.cursor()
    
    print("\n" + "="*70)
    print("STEP 6: Finding references to ai_audit by ID")
    print("="*70)
    
    # Get a sample ai_audit ID
    cursor.execute("SELECT id FROM ai_audit LIMIT 1")
    result = cursor.fetchone()
    
    if not result:
        print("⚠️  No data in ai_audit table")
        cursor.close()
        conn.close()
        return
    
    sample_id = result[0]
    print(f"\nUsing sample ai_audit ID: {sample_id}")
    
    # Find columns that might reference ai_audit
    cursor.execute("""
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND (
            column_name LIKE '%ai_audit%'
            OR column_name LIKE '%audit_id%'
            OR column_name = 'ai_id'
          )
    """)
    
    ref_columns = cursor.fetchall()
    
    print("\nColumns that might reference ai_audit:")
    for table, col in ref_columns:
        print(f"  {table}.{col}")
        
        # Try to find matching records
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} = %s", (sample_id,))
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"    ✓ Found {count} matching records!")
                
                # Show sample
                cursor.execute(f"SELECT * FROM {table} WHERE {col} = %s LIMIT 1", (sample_id,))
                row = cursor.fetchone()
                if row:
                    cols = [desc[0] for desc in cursor.description]
                    print(f"    Sample record:")
                    for c, v in zip(cols, row):
                        print(f"      {c}: {str(v)[:100]}")
        except Exception as e:
            pass
    
    cursor.close()
    conn.close()


def main():
    print("\n🔍 Exploring OpenGov Database for AI Response Data")
    print("="*70)
    
    try:
        # Run all explorations
        explore_ai_audit()
        related_tables = find_foreign_keys_to_ai_audit()
        find_tables_with_ai_columns()
        explore_project_tables()
        sample_long_text_columns()
        find_ai_audit_id_usage()
        
        print("\n" + "="*70)
        print("✓ Exploration Complete!")
        print("="*70)
        print("\nNext steps:")
        print("1. Review the output above")
        print("2. Look for tables/columns that contain AI responses")
        print("3. Check if response is in ai_audit itself or a related table")
        print("4. Look for JSON columns that might have response data")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

