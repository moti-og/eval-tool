"""
Verify if section_description content is ONLY AI-generated
or if it includes human edits/template content
"""

import psycopg2

POSTGRES_URL = "postgresql://usr_teleport_reader@localhost:51329/procurement_prod"

conn = psycopg2.connect(POSTGRES_URL)
cursor = conn.cursor()

print("="*70)
print("VERIFYING AI vs HUMAN CONTENT")
print("="*70)

# Compare timestamps: ai_audit vs section_description
cursor.execute("""
    SELECT 
        a.id as ai_id,
        a.prompt,
        a.created_at as ai_created,
        sd.created_at as section_created,
        sd.updated_at as section_updated,
        (sd.updated_at - a.created_at) as time_diff,
        sd.description
    FROM ai_audit a
    JOIN section_description sd ON a.project_id = sd.project_id
    WHERE sd.description IS NOT NULL
    ORDER BY a.created_at DESC
    LIMIT 10
""")

print("\nTimestamp Comparison (AI creation vs Section creation/update):")
print("-"*70)

results = cursor.fetchall()
for ai_id, prompt, ai_created, sec_created, sec_updated, time_diff, description in results:
    print(f"\nAI Audit #{ai_id}: {prompt[:50]}...")
    print(f"  AI created: {ai_created}")
    print(f"  Section created: {sec_created}")
    print(f"  Section updated: {sec_updated}")
    print(f"  Time difference: {time_diff}")
    
    if sec_created and ai_created:
        if abs((sec_created - ai_created).total_seconds()) < 5:
            print(f"  ✓ Likely AI-generated (created within 5 seconds)")
        else:
            print(f"  ⚠️  Created {abs((sec_created - ai_created).total_seconds())} seconds apart")
    
    if sec_updated and sec_created:
        if (sec_updated - sec_created).total_seconds() > 60:
            print(f"  ⚠️  WARNING: Section was updated {(sec_updated - sec_created).total_seconds()/60:.1f} minutes after creation")
            print(f"     This might include human edits!")

# Check if there are section_descriptions WITHOUT corresponding ai_audit entries
cursor.execute("""
    SELECT COUNT(*) as total_sections,
           COUNT(CASE WHEN a.id IS NOT NULL THEN 1 END) as with_ai_audit,
           COUNT(CASE WHEN a.id IS NULL THEN 1 END) as without_ai_audit
    FROM section_description sd
    LEFT JOIN ai_audit a ON sd.project_id = a.project_id
    WHERE sd.description IS NOT NULL
""")

total, with_ai, without_ai = cursor.fetchone()

print("\n" + "="*70)
print("SECTION DESCRIPTIONS ANALYSIS")
print("="*70)
print(f"Total section_descriptions: {total:,}")
print(f"  With ai_audit link: {with_ai:,} ({with_ai/total*100:.1f}%)")
print(f"  WITHOUT ai_audit: {without_ai:,} ({without_ai/total*100:.1f}%)")

if without_ai > 0:
    print(f"\n⚠️  WARNING: {without_ai:,} sections have no AI audit record!")
    print("   These are likely manually created, not AI-generated.")

# Check for patterns that indicate AI vs template
cursor.execute("""
    SELECT 
        a.id,
        a.prompt,
        sd.description,
        LENGTH(sd.description) as length
    FROM ai_audit a
    JOIN section_description sd ON a.project_id = sd.project_id
    WHERE sd.description IS NOT NULL
    ORDER BY RANDOM()
    LIMIT 3
""")

print("\n" + "="*70)
print("SAMPLE CONTENT ANALYSIS")
print("="*70)

for ai_id, prompt, description, length in cursor.fetchall():
    print(f"\nPrompt: {prompt}")
    print(f"Content length: {length} characters")
    print(f"Preview: {description[:200]}...")
    
    # Look for template indicators
    if '{{' in description or '}}' in description:
        print("  ⚠️  Contains template placeholders")
    if description.count('<p>') > 5:
        print("  ℹ️  Heavily formatted HTML (common in AI generation)")
    if 'shall procure and maintain' in description.lower():
        print("  ℹ️  Contains boilerplate legal language")

conn.close()

print("\n" + "="*70)
print("RECOMMENDATION")
print("="*70)
print("""
Based on the analysis above:

1. If timestamps are close (< 5 seconds): Likely pure AI content ✓
2. If section was updated later: May include human edits ⚠️
3. If no ai_audit link: Probably not AI-generated ⚠️

BEST PRACTICE:
- Only load sections where ai_audit.created_at ~= section_description.created_at
- Filter out sections that were updated significantly after creation
- Add a flag to indicate "potentially edited"
""")

