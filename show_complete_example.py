"""
Show a complete example of prompt + AI response
"""

import psycopg2

POSTGRES_URL = "postgresql://usr_teleport_reader@localhost:51329/procurement_prod"

conn = psycopg2.connect(POSTGRES_URL)
cursor = conn.cursor()

# Get an AI audit with descriptions
cursor.execute("""
    SELECT a.id, a.prompt, a.project_id
    FROM ai_audit a
    WHERE a.id = 9218
""")

ai_id, prompt, project_id = cursor.fetchone()

print("="*70)
print("COMPLETE AI INTERACTION EXAMPLE")
print("="*70)

print(f"\n📝 AI Audit ID: {ai_id}")
print(f"\n💬 USER PROMPT:")
print(f"   {prompt}")

print(f"\n🎯 PROJECT ID: {project_id}")

# Get all section descriptions for this project
cursor.execute("""
    SELECT 
        ps.title as section_title,
        pss.title as subsection_title,
        sd.description,
        sd.created_at
    FROM section_description sd
    LEFT JOIN project_section ps ON sd.project_section_id = ps.id
    LEFT JOIN project_subsection pss ON sd.project_subsection_id = pss.id
    WHERE sd.project_id = %s
    ORDER BY sd.created_at
""", (project_id,))

descriptions = cursor.fetchall()

print(f"\n🤖 AI RESPONSES ({len(descriptions)} sections generated):")
print("="*70)

for i, (sec_title, subsec_title, description, created_at) in enumerate(descriptions, 1):
    title = subsec_title or sec_title or "Unknown"
    print(f"\n{i}. {title}")
    print(f"   Created: {created_at}")
    if description:
        # Show first 500 chars
        desc_preview = description[:500]
        print(f"   Content: {desc_preview}...")
        print()

conn.close()

print("\n" + "="*70)
print("CONFIRMED!")
print("="*70)
print("""
✓ ai_audit.prompt = User's input
✓ section_description.description = AI's generated content
✓ Linked via project_id

This is what we need to load into the review tool!
""")

