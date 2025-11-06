"""
Find where AI responses are stored by looking at specific projects
"""

import psycopg2

POSTGRES_URL = "postgresql://usr_teleport_reader@localhost:51329/procurement_prod"

def check_project_for_ai_response():
    """Look at the actual project data for AI audit entries"""
    conn = psycopg2.connect(POSTGRES_URL)
    cursor = conn.cursor()
    
    print("="*70)
    print("Finding AI Response Location")
    print("="*70)
    
    # Get a sample ai_audit entry with its project_id
    cursor.execute("""
        SELECT id, prompt, project_id, government_id
        FROM ai_audit
        LIMIT 5
    """)
    
    ai_audits = cursor.fetchall()
    
    print("\nSample AI audit entries:")
    for aid, prompt, pid, gid in ai_audits:
        print(f"\nai_audit ID: {aid}")
        print(f"  Prompt: {prompt}")
        print(f"  Project ID: {pid}")
        
        # Get columns in project table
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'project'
            ORDER BY ordinal_position
        """)
        
        project_cols = cursor.fetchall()
        
        # Get the actual project data
        cursor.execute(f"""
            SELECT *
            FROM project
            WHERE id = %s
        """, (pid,))
        
        project_data = cursor.fetchone()
        
        if project_data:
            print(f"\n  Project {pid} data:")
            col_names = [desc[0] for desc in cursor.description]
            
            for col_name, value in zip(col_names, project_data):
                # Show text/content columns
                if value and isinstance(value, str) and len(value) > 50:
                    print(f"    {col_name}: {str(value)[:200]}...")
                elif value:
                    print(f"    {col_name}: {value}")
        
        # Check project_section table
        cursor.execute("""
            SELECT id, name, content
            FROM project_section
            WHERE project_id = %s
            LIMIT 3
        """, (pid,))
        
        sections = cursor.fetchall()
        if sections:
            print(f"\n  Project sections:")
            for sec_id, sec_name, sec_content in sections:
                if sec_content:
                    print(f"    Section '{sec_name}': {str(sec_content)[:200]}...")
        
        # Check project_subsection table
        cursor.execute("""
            SELECT ps.name as section_name, pss.name as subsection_name, pss.content
            FROM project_subsection pss
            JOIN project_section ps ON pss.project_section_id = ps.id
            WHERE ps.project_id = %s
            LIMIT 3
        """, (pid,))
        
        subsections = cursor.fetchall()
        if subsections:
            print(f"\n  Project subsections:")
            for sec_name, subsec_name, content in subsections:
                if content:
                    print(f"    {sec_name} > {subsec_name}: {str(content)[:200]}...")
        
        print("\n" + "-"*70)
    
    cursor.close()
    conn.close()


def check_government_ai_data():
    """Check if there's AI response data in government table"""
    conn = psycopg2.connect(POSTGRES_URL)
    cursor = conn.cursor()
    
    print("\n" + "="*70)
    print("Checking government.ai_enablement_data")
    print("="*70)
    
    cursor.execute("""
        SELECT id, name, ai_enablement_data
        FROM government
        WHERE ai_enablement_data IS NOT NULL
        LIMIT 3
    """)
    
    results = cursor.fetchall()
    
    for gov_id, gov_name, ai_data in results:
        print(f"\nGovernment: {gov_name} (ID: {gov_id})")
        print(f"AI Data: {ai_data}")
    
    cursor.close()
    conn.close()


if __name__ == '__main__':
    check_project_for_ai_response()
    check_government_ai_data()
    
    print("\n" + "="*70)
    print("Analysis:")
    print("="*70)
    print("""
Based on the data above, the AI response is likely in:

1. project table - check for description/content/scope fields
2. project_section.content - AI might generate section content
3. project_subsection.content - AI might generate subsection content

The 'prompt' in ai_audit appears to be what the user enters,
and the AI likely generates content that populates the project.
    """)

