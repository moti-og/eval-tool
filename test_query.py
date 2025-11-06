import psycopg2

conn = psycopg2.connect('postgresql://usr_teleport_reader@localhost:51329/procurement_prod')
cursor = conn.cursor()

# Test the exact query
query = """
SELECT COUNT(*) 
FROM ai_audit a
JOIN section_description sd ON a.project_id = sd.project_id
WHERE sd.created_at::timestamp > a.created_at::timestamp
  AND sd.created_at::timestamp < (a.created_at::timestamp + INTERVAL '1 hour')
  AND sd.description IS NOT NULL
  AND LENGTH(sd.description) > 50
"""

cursor.execute(query)
count = cursor.fetchone()[0]
print(f'Total AI interactions with valid content: {count}')

# Get a sample
query2 = """
SELECT a.id, a.prompt, a.created_at, sd.created_at
FROM ai_audit a
JOIN section_description sd ON a.project_id = sd.project_id
WHERE sd.created_at::timestamp > a.created_at::timestamp
  AND sd.created_at::timestamp < (a.created_at::timestamp + INTERVAL '1 hour')
  AND sd.description IS NOT NULL
LIMIT 5
"""

cursor.execute(query2)
print('\nSample results:')
for ai_id, prompt, ai_time, sd_time in cursor.fetchall():
    print(f'AI #{ai_id}: {prompt[:40]}... ({ai_time} -> {sd_time})')

conn.close()

