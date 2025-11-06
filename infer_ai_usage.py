"""
Infer AI-driven content by matching ai_audit prompts with criteria saves

Logic:
- ai_audit = User requested AI to generate something
- criteria created/updated soon after = User likely saved (and maybe edited) the AI output
- We can't prove it's pure AI, but it's our best indicator
"""

import psycopg2

POSTGRES_URL = "postgresql://usr_teleport_reader@localhost:51329/procurement_prod"

conn = psycopg2.connect(POSTGRES_URL)
cursor = conn.cursor()

print("="*70)
print("INFERRING AI-DRIVEN CONTENT FROM CRITERIA")
print("="*70)

# Check criteria table structure first
cursor.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'criteria'
    ORDER BY ordinal_position
""")

print("\nCriteria table structure:")
for col, dtype in cursor.fetchall():
    print(f"  {col:<30} {dtype}")

print("\n" + "="*70)
print("STRATEGY: Find criteria CREATED (not just updated) after AI prompt")
print("="*70)
print("Rationale: created_at = new content added (higher confidence)")
print("           updated_at = might be unrelated edit (lower confidence)")

# Find criteria CREATED within 15 minutes of AI audit
cursor.execute("""
    SELECT 
        a.id as ai_audit_id,
        a.prompt,
        a.created_at as ai_time,
        c.id as criteria_id,
        c.description,
        c.created_at as criteria_created,
        c.updated_at as criteria_updated,
        EXTRACT(EPOCH FROM (c.created_at::timestamp - a.created_at::timestamp))/60 as minutes_after
    FROM ai_audit a
    JOIN project p ON a.project_id = p.id
    JOIN project_section ps ON p.id = ps.project_id
    JOIN criteria c ON ps.id = c.project_section_id
    WHERE c.created_at::timestamp BETWEEN a.created_at::timestamp AND (a.created_at::timestamp + INTERVAL '15 minutes')
      AND c.description IS NOT NULL
      AND LENGTH(c.description) > 100
    ORDER BY a.created_at DESC
    LIMIT 30
""")

results = cursor.fetchall()

print(f"\n✓ Found {len(results)} criteria CREATED within 15 min of AI prompt:")
print("="*70)

if results:
    # Group by AI audit to see how many criteria per prompt
    from collections import defaultdict
    ai_groups = defaultdict(list)
    
    for row in results:
        ai_id = row[0]
        ai_groups[ai_id].append(row)
    
    print(f"\nGrouped into {len(ai_groups)} unique AI prompts:\n")
    
    for ai_id, group in list(ai_groups.items())[:10]:  # Show first 10
        first_row = group[0]
        ai_id, prompt, ai_time, _, _, _, _, _ = first_row
        
        print(f"🎯 AI Audit #{ai_id}")
        print(f"   Prompt: {prompt[:70]}...")
        print(f"   AI time: {ai_time}")
        print(f"   Criteria created: {len(group)}")
        
        for row in group[:3]:  # Show first 3 criteria
            _, _, _, crit_id, description, created, updated, mins = row
            print(f"   ✓ Criteria #{crit_id}: Created {mins:.1f} min later")
            print(f"     Content: {description[:150]}...")
        
        if len(group) > 3:
            print(f"   ... and {len(group)-3} more")
        print()

else:
    print("\n⚠️  No criteria found that were CREATED shortly after AI prompts")
    print("   Trying with updated_at instead...")
    
    # Fallback: Try updated_at
    cursor.execute("""
        SELECT 
            a.id,
            a.prompt,
            COUNT(c.id) as criteria_count
        FROM ai_audit a
        JOIN project p ON a.project_id = p.id
        JOIN project_section ps ON p.id = ps.project_id
        JOIN criteria c ON ps.id = c.project_section_id
        WHERE c.updated_at::timestamp BETWEEN a.created_at::timestamp AND (a.created_at::timestamp + INTERVAL '15 minutes')
        GROUP BY a.id, a.prompt
        ORDER BY a.created_at DESC
        LIMIT 10
    """)
    
    fallback = cursor.fetchall()
    if fallback:
        print(f"\n   Found {len(fallback)} AI audits with criteria UPDATED nearby:")
        for ai_id, prompt, count in fallback:
            print(f"   - AI #{ai_id}: {count} criteria - {prompt[:50]}...")

# Get statistics
cursor.execute("""
    SELECT 
        COUNT(DISTINCT a.id) as total_ai_audits,
        COUNT(DISTINCT c.id) as total_criteria,
        COUNT(DISTINCT CASE 
            WHEN c.created_at::timestamp BETWEEN a.created_at::timestamp 
                AND (a.created_at::timestamp + INTERVAL '15 minutes') 
            THEN a.id END) as ai_with_criteria
    FROM ai_audit a
    LEFT JOIN project p ON a.project_id = p.id
    LEFT JOIN project_section ps ON p.id = ps.project_id
    LEFT JOIN criteria c ON ps.id = c.project_section_id
""")

total_ai, total_crit, ai_with_crit = cursor.fetchone()

print("\n" + "="*70)
print("STATISTICS")
print("="*70)
print(f"Total ai_audit records: {total_ai:,}")
print(f"Total criteria linked to AI projects: {total_crit:,}")
print(f"AI audits with criteria created within 15 min: {ai_with_crit:,}")
if total_ai > 0:
    print(f"Percentage with likely AI usage: {ai_with_crit/total_ai*100:.1f}%")

conn.close()

print("\n" + "="*70)
print("INTERPRETATION")
print("="*70)
print("""
✓ HIGH CONFIDENCE: Criteria created 0-5 minutes after prompt
   → User likely accepted AI output quickly

⚠️  MEDIUM CONFIDENCE: Criteria created 5-15 minutes after prompt
   → User may have reviewed/edited before saving

❌ LOW CONFIDENCE: Criteria updated (not created) after prompt
   → Might be unrelated edit

RECOMMENDATION:
- Load criteria created within 0-15 minutes of ai_audit
- Flag with confidence level based on timing
- Add notes about potential human editing
""")

