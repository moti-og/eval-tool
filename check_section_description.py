"""
Check section_description table - likely where AI responses are stored
"""

import psycopg2

POSTGRES_URL = "postgresql://usr_teleport_reader@localhost:51329/procurement_prod"

conn = psycopg2.connect(POSTGRES_URL)
cursor = conn.cursor()

print("="*70)
print("SECTION_DESCRIPTION TABLE")
print("="*70)

# Get schema
cursor.execute("""
    SELECT column_name, data_type, character_maximum_length
    FROM information_schema.columns 
    WHERE table_name = 'section_description'
    ORDER BY ordinal_position
""")

print("\nColumns:")
print("-"*70)
for col, dtype, max_len in cursor.fetchall():
    len_str = f"({max_len})" if max_len else ""
    print(f"  {col:<30} {dtype}{len_str}")

# Get sample data
cursor.execute("SELECT * FROM section_description LIMIT 3")
rows = cursor.fetchall()
cols = [desc[0] for desc in cursor.description]

print("\nSample data:")
print("="*70)
for i, row in enumerate(rows, 1):
    print(f"\nRow {i}:")
    for col, val in zip(cols, row):
        if val:
            val_str = str(val)[:200] if isinstance(val, str) else str(val)
            print(f"  {col}: {val_str}")

# Link to ai_audit
print("\n" + "="*70)
print("LINKING TO AI_AUDIT")
print("="*70)

cursor.execute("""
    SELECT 
        a.id as ai_audit_id,
        a.prompt,
        a.project_id,
        ps.id as project_section_id,
        ps.title as section_title,
        sd.description,
        sd.shared_id
    FROM ai_audit a
    JOIN project_section ps ON a.project_id = ps.project_id
    LEFT JOIN section_description sd ON ps.id = sd.project_section_id
    LIMIT 5
""")

print("\nAI Audit → Project Section → Section Description:")
print("-"*70)
results = cursor.fetchall()
for ai_id, prompt, proj_id, sect_id, sect_title, description, shared_id in results:
    print(f"\nAI Audit {ai_id}:")
    print(f"  Prompt: {prompt}")
    print(f"  Project ID: {proj_id}")
    print(f"  Section: {sect_title}")
    if description:
        print(f"  Description: {description[:300]}...")
        print(f"  ⭐ THIS MIGHT BE THE AI RESPONSE!")

conn.close()

print("\n" + "="*70)
print("CONCLUSION")
print("="*70)
print("""
If section_description.description contains long generated text,
that's likely where the AI responses are stored!

The flow is:
1. User enters prompt → ai_audit.prompt
2. AI generates content → section_description.description
3. Linked by: ai_audit.project_id → project_section.project_id → section_description.project_section_id
""")

