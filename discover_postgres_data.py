"""
Discover LLM data in your PostgreSQL database

This script helps you find where LLM/AI data is stored in your OpenGov database.
Run this first to understand your data before importing.
"""

import psycopg2
from psycopg2 import sql
import json
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()


class PostgresDataDiscovery:
    """Discover and explore LLM data in Postgres"""
    
    def __init__(self, connection_string=None):
        self.connection_string = connection_string or os.getenv('POSTGRES_URL')
        if not self.connection_string:
            print("❌ POSTGRES_URL not found in .env file")
            print("\nAdd this to your .env file:")
            print("POSTGRES_URL=postgresql://username:password@host:port/database")
            raise ValueError("POSTGRES_URL required")
        
        print(f"✓ Connecting to database...")
        try:
            self.conn = psycopg2.connect(self.connection_string)
            print(f"✓ Connected successfully!\n")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            raise
    
    def find_llm_tables(self):
        """
        Find tables that might contain LLM/AI data
        """
        print("="*60)
        print("STEP 1: Finding tables with LLM/AI data")
        print("="*60)
        
        cursor = self.conn.cursor()
        
        # Search for tables with relevant names
        cursor.execute("""
            SELECT 
                table_name,
                (SELECT COUNT(*) 
                 FROM information_schema.columns 
                 WHERE table_name = t.table_name 
                 AND table_schema = 'public') as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public' 
              AND table_type = 'BASE TABLE'
              AND (
                table_name LIKE '%llm%' 
                OR table_name LIKE '%ai%'
                OR table_name LIKE '%gpt%'
                OR table_name LIKE '%prompt%'
                OR table_name LIKE '%conversation%'
                OR table_name LIKE '%chat%'
                OR table_name LIKE '%message%'
                OR table_name LIKE '%response%'
                OR table_name LIKE '%completion%'
              )
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        
        if tables:
            print(f"\n✓ Found {len(tables)} potentially relevant tables:\n")
            for i, (table, col_count) in enumerate(tables, 1):
                print(f"  {i}. {table} ({col_count} columns)")
            return [t[0] for t in tables]
        else:
            print("⚠️  No tables found with obvious LLM-related names")
            print("\nLet's look at ALL tables...\n")
            return self.list_all_tables()
        
        cursor.close()
    
    def list_all_tables(self):
        """List all tables in the database"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                table_name,
                (SELECT COUNT(*) 
                 FROM information_schema.columns 
                 WHERE table_name = t.table_name 
                 AND table_schema = 'public') as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public' 
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
            LIMIT 50
        """)
        
        tables = cursor.fetchall()
        
        print(f"Found {len(tables)} tables (showing first 50):\n")
        for i, (table, col_count) in enumerate(tables, 1):
            print(f"  {i}. {table} ({col_count} columns)")
        
        cursor.close()
        return [t[0] for t in tables]
    
    def inspect_table_schema(self, table_name):
        """
        Show detailed schema for a specific table
        """
        print(f"\n{'='*60}")
        print(f"INSPECTING TABLE: {table_name}")
        print(f"{'='*60}\n")
        
        cursor = self.conn.cursor()
        
        # Get columns
        cursor.execute("""
            SELECT 
                column_name, 
                data_type,
                character_maximum_length,
                is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public' 
              AND table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        
        columns = cursor.fetchall()
        
        print("Columns:")
        print("-" * 60)
        for col_name, data_type, max_len, nullable in columns:
            type_str = data_type
            if max_len:
                type_str += f"({max_len})"
            nullable_str = "NULL" if nullable == "YES" else "NOT NULL"
            print(f"  {col_name:<30} {type_str:<20} {nullable_str}")
        
        # Get row count
        cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(
            sql.Identifier(table_name)
        ))
        row_count = cursor.fetchone()[0]
        print(f"\nTotal rows: {row_count:,}")
        
        cursor.close()
        return columns
    
    def sample_table_data(self, table_name, limit=3):
        """
        Show sample data from a table
        """
        print(f"\n{'='*60}")
        print(f"SAMPLE DATA FROM: {table_name} (first {limit} rows)")
        print(f"{'='*60}\n")
        
        cursor = self.conn.cursor()
        
        try:
            cursor.execute(sql.SQL("SELECT * FROM {} LIMIT %s").format(
                sql.Identifier(table_name)
            ), (limit,))
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            if not rows:
                print("⚠️  Table is empty")
                return
            
            for i, row in enumerate(rows, 1):
                print(f"Row {i}:")
                for col, val in zip(columns, row):
                    # Truncate long values
                    val_str = str(val)
                    if len(val_str) > 100:
                        val_str = val_str[:100] + "..."
                    print(f"  {col}: {val_str}")
                print()
        
        except Exception as e:
            print(f"❌ Error sampling data: {e}")
        
        cursor.close()
    
    def find_columns_with_keywords(self, keywords=None):
        """
        Find columns that might contain prompts/responses
        """
        if not keywords:
            keywords = ['prompt', 'response', 'message', 'text', 'content', 
                       'input', 'output', 'llm', 'ai', 'query', 'answer']
        
        print(f"\n{'='*60}")
        print(f"FINDING COLUMNS WITH KEYWORDS: {', '.join(keywords)}")
        print(f"{'='*60}\n")
        
        cursor = self.conn.cursor()
        
        # Build the WHERE clause dynamically
        conditions = " OR ".join([f"column_name LIKE '%{kw}%'" for kw in keywords])
        
        cursor.execute(f"""
            SELECT 
                table_name,
                column_name,
                data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND ({conditions})
            ORDER BY table_name, column_name
        """)
        
        results = cursor.fetchall()
        
        if results:
            print(f"Found {len(results)} relevant columns:\n")
            current_table = None
            for table, column, dtype in results:
                if table != current_table:
                    print(f"\n📋 Table: {table}")
                    current_table = table
                print(f"   - {column} ({dtype})")
        else:
            print("⚠️  No columns found matching keywords")
        
        cursor.close()
        return results
    
    def search_for_json_columns(self):
        """
        Find JSON/JSONB columns (often used for AI data)
        """
        print(f"\n{'='*60}")
        print(f"FINDING JSON COLUMNS")
        print(f"{'='*60}\n")
        
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                table_name,
                column_name,
                data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND data_type IN ('json', 'jsonb')
            ORDER BY table_name, column_name
        """)
        
        results = cursor.fetchall()
        
        if results:
            print(f"Found {len(results)} JSON columns:\n")
            for table, column, dtype in results:
                print(f"  {table}.{column} ({dtype})")
        else:
            print("⚠️  No JSON columns found")
        
        cursor.close()
        return results
    
    def generate_sample_query(self, table_name, columns):
        """
        Generate a sample SQL query based on discovered schema
        """
        print(f"\n{'='*60}")
        print(f"GENERATED SAMPLE QUERY FOR: {table_name}")
        print(f"{'='*60}\n")
        
        # Try to identify key columns
        col_names = [c[0] for c in columns]
        
        # Look for common column names
        id_col = next((c for c in col_names if c in ['id', 'uuid', 'pk']), col_names[0])
        prompt_col = next((c for c in col_names if 'prompt' in c.lower() or 'input' in c.lower() or 'query' in c.lower()), None)
        response_col = next((c for c in col_names if 'response' in c.lower() or 'output' in c.lower() or 'answer' in c.lower()), None)
        timestamp_col = next((c for c in col_names if 'created' in c.lower() or 'timestamp' in c.lower() or 'date' in c.lower()), None)
        
        query = f"""
SELECT 
    {id_col} as id,
    {f"{prompt_col} as user_prompt," if prompt_col else "-- ADD PROMPT COLUMN HERE"}
    {f"{response_col} as llm_response," if response_col else "-- ADD RESPONSE COLUMN HERE"}
    {f"{timestamp_col} as created_at" if timestamp_col else "-- ADD TIMESTAMP COLUMN HERE"}
FROM {table_name}
{f"WHERE {timestamp_col} >= NOW() - INTERVAL '7 days'" if timestamp_col else "-- WHERE ..."}
ORDER BY {timestamp_col if timestamp_col else id_col} DESC
LIMIT 50;
"""
        
        print(query)
        
        # Save to file
        queries_dir = Path("queries")
        queries_dir.mkdir(exist_ok=True)
        
        query_file = queries_dir / f"{table_name}_query.sql"
        query_file.write_text(query)
        
        print(f"\n✓ Saved to: {query_file}")
        
        return query
    
    def interactive_discovery(self):
        """
        Run interactive discovery process
        """
        print("\n🔍 PostgreSQL LLM Data Discovery Tool")
        print("=" * 60)
        
        # Step 1: Find relevant tables
        tables = self.find_llm_tables()
        
        if not tables:
            print("\n⚠️  Could not find obvious LLM data")
            print("Tips:")
            print("  1. Ask your team which tables store AI/LLM data")
            print("  2. Look for audit logs or api_logs tables")
            print("  3. Check if data is in a separate service/database")
            return
        
        # Step 2: Find relevant columns
        print("\n" + "="*60)
        self.find_columns_with_keywords()
        
        # Step 3: Check JSON columns
        self.search_for_json_columns()
        
        # Step 4: Let user pick a table to inspect
        print("\n" + "="*60)
        print("Which table would you like to inspect?")
        print("Enter table number (or 'q' to quit):")
        
        for i, table in enumerate(tables, 1):
            print(f"  {i}. {table}")
        
        try:
            choice = input("\nYour choice: ").strip()
            
            if choice.lower() == 'q':
                return
            
            table_idx = int(choice) - 1
            if 0 <= table_idx < len(tables):
                table_name = tables[table_idx]
                
                # Show schema
                columns = self.inspect_table_schema(table_name)
                
                # Show sample data
                self.sample_table_data(table_name, limit=3)
                
                # Generate query
                self.generate_sample_query(table_name, columns)
                
                print("\n" + "="*60)
                print("✓ Discovery complete!")
                print("="*60)
                print("\nNext steps:")
                print("  1. Review the sample data above")
                print("  2. Edit the generated query in queries/ folder")
                print("  3. Use it in load_from_postgres.py")
                print("  4. Run: python load_from_postgres.py")
            else:
                print("Invalid choice")
        
        except (ValueError, IndexError):
            print("Invalid input")
        except KeyboardInterrupt:
            print("\n\nExiting...")


def main():
    """
    Run the discovery tool
    
    Usage:
        python discover_postgres_data.py
    """
    
    try:
        discovery = PostgresDataDiscovery()
        discovery.interactive_discovery()
    
    except ValueError as e:
        print(f"\n{e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())

