"""
Find AI-generated content in criteria table by matching timestamps
"""

import psycopg2

POSTGRES_URL = "postgresql://usr_teleport_reader@localhost:51329/procurement_prod"

conn = psycopg2.connect(POSTGRES_URL)
cursor = conn.cursor()

print("="*70)
print("FINDING AI-GENERATED CRITERIA")
print("="*70)

# First, check the criteria table structure
cursor.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'criteria'
    ORDER BY ordinal_position
""")

print("\nCriteria table columns:")
print("-"*70)
for col, dtype in cursor.fetchall():
    print(f"  {col:<30} {dtype}")

# Find criteria that were created/updated within 15 minutes of an AI audit
cursor.execute("""
    SELECT 
        a.id as ai_audit_id,
        a.prompt,
        a.created_at as ai_time,
        c.id as criteria_id,
        c.description,
        c.created_at as criteria_created,
        c.updated_at as criteria_updated,
        EXTRACT(EPOCH FROM (c.created_at::timestamp - a.created_at::timestamp))/60 as create_diff_minutes,
        EXTRACT(EPOCH FROM (c.updated_at::timestamp - a.created_at::timestamp))/60 as update_diff_minutes
    FROM ai_audit a
    JOIN project p ON a.project_id = p.id
    JOIN project_section ps ON p.id = ps.project_id
    JOIN criteria c ON ps.id = c.project_section_id
    WHERE (
        c.created_at::timestamp BETWEEN a.created_at::timestamp AND (a.created_at::timestamp + INTERVAL '15 minutes')
        OR
        c.updated_at::timestamp BETWEEN a.created_at::timestamp AND (a.created_at::timestamp + INTERVAL '15 minutes')
    )
    AND c.description IS NOT NULL
    AND LENGTH(c.description) > 50
    ORDER BY a.created_at DESC
    LIMIT 20
""")

results = cursor.fetchall()

print(f"\n✓ Found {len(results)} criteria updated within 15 minutes of AI prompts:")
print("="*70)

if results:
    for ai_id, prompt, ai_time, crit_id, description, created, updated, create_diff, update_diff in results:
        print(f"\n🎯 AI Audit #{ai_id}")
        print(f"   Prompt: {prompt[:60]}...")
        print(f"   AI time: {ai_time}")
        
        if create_diff and 0 <= create_diff <= 15:
            print(f"   ✓ Criteria CREATED {create_diff:.1f} minutes after prompt")
            print(f"     Created: {created}")
        
        if update_diff and 0 <= update_diff <= 15:
            print(f"   ✓ Criteria UPDATED {update_diff:.1f} minutes after prompt")
            print(f"     Updated: {updated}")
        
        print(f"   Content preview: {description[:200]}...")
        print()
else:
    print("\n⚠️  No criteria found within 15 minutes of AI prompts")

# Get total counts
cursor.execute("""
    SELECT COUNT(DISTINCT a.id)
    FROM ai_audit a
    JOIN project p ON a.project_id = p.id
    JOIN project_section ps ON p.id = ps.project_id
    JOIN criteria c ON ps.id = c.project_section_id
    WHERE (
        c.created_at::timestamp BETWEEN a.created_at::timestamp AND (a.created_at::timestamp + INTERVAL '15 minutes')
        OR
        c.updated_at::timestamp BETWEEN a.created_at::timestamp AND (a.created_at::timestamp + INTERVAL '15 minutes')
    )
""")

total_ai_with_criteria = cursor.fetchone()[0]

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"Total AI audits with criteria updated within 15 min: {total_ai_with_criteria}")

# Check how many criteria each AI prompt typically generates
cursor.execute("""
    SELECT 
        a.id,
        a.prompt,
        COUNT(c.id) as criteria_count
    FROM ai_audit a
    JOIN project p ON a.project_id = p.id
    JOIN project_section ps ON p.id = ps.project_id
    JOIN criteria c ON ps.id = c.project_section_id
    WHERE (
        c.created_at::timestamp BETWEEN a.created_at::timestamp AND (a.created_at::timestamp + INTERVAL '15 minutes')
        OR
        c.updated_at::timestamp BETWEEN a.created_at::timestamp AND (a.created_at::timestamp + INTERVAL '15 minutes')
    )
    GROUP BY a.id, a.prompt
    ORDER BY criteria_count DESC
    LIMIT 5
""")

print("\nTop AI prompts by number of criteria generated:")
print("-"*70)
for ai_id, prompt, count in cursor.fetchall():
    print(f"  AI #{ai_id}: {count} criteria - {prompt[:50]}...")

conn.close()

print("\n" + "="*70)
print("NEXT STEP")
print("="*70)
print("""
If we found criteria matching AI audit timestamps, that's where the
AI-generated content is stored!

We can now load these for human review.
""")

