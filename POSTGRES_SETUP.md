# PostgreSQL Integration Guide

Complete guide to connect your OpenGov Postgres database to the review tool.

## 🎯 Two Phases

### Phase 1: Test with Existing Data
Pull existing LLM conversations from Postgres and review them

### Phase 2: Live Integration
Hook up to your application and save reviews to database

---

## 📋 Prerequisites

1. **Postgres connection details**:
   - Host
   - Port
   - Database name
   - Username
   - Password

2. **Install Postgres driver**:
```bash
pip install psycopg2-binary
```

---

## 🚀 Phase 1: Load Existing Data

### Step 1: Configure Database Connection

Add to your `.env` file:

```bash
# PostgreSQL Connection
POSTGRES_URL=postgresql://username:password@host:port/database

# Example:
# POSTGRES_URL=postgresql://admin:mypass@opengov-db.us-west-2.rds.amazonaws.com:5432/opengov_prod
```

### Step 2: Customize the Query

Edit `load_from_postgres.py` to match your table structure:

```python
# Find this section and update with your actual table/column names:
query = """
SELECT 
    id,
    user_prompt,          -- Your column name for user input
    llm_response,         -- Your column name for LLM output
    context_data,         -- Any additional context
    model_name,           -- Which model was used
    feature_name,         -- Which feature (budget_analysis, etc.)
    user_id,
    created_at
FROM llm_conversations   -- Your table name
WHERE created_at >= NOW() - INTERVAL '7 days'
ORDER BY created_at DESC
LIMIT 50
"""
```

### Step 3: Run the Loader

```bash
python load_from_postgres.py
```

This will:
- ✓ Connect to your Postgres database
- ✓ Pull the last 50 LLM conversations
- ✓ Load them into the review queue
- ✓ You can then review them in the UI

### Step 4: Review the Data

```bash
streamlit run human_review_app.py
```

Navigate to http://localhost:8069 and start reviewing!

---

## 🔧 Phase 2: Save Reviews to Database

### Step 1: Create Reviews Table

Run this to create the table for storing reviews:

```bash
python save_reviews_to_db.py
```

This creates a table called `llm_human_reviews` with:
- Review ID
- Original conversation data
- Acceptable/Not Acceptable rating
- Notes and tags
- Timestamps

### Step 2: Auto-Sync Reviews

Option A: **Manual sync** (run periodically):
```bash
python save_reviews_to_db.py
```

Option B: **Auto-sync** (add to your review app):

Edit `human_review_app.py`, find the `save_review()` call and add:

```python
# After this line:
storage.save_review(review_data)

# Add this:
try:
    from save_reviews_to_db import ReviewDatabaseSaver
    db_saver = ReviewDatabaseSaver()
    db_saver.save_review(review_data)
except Exception as e:
    print(f"Warning: Could not save to database: {e}")
```

---

## 📊 Common Database Schemas

### Example 1: If your LLM data is in a logs table

```python
query = """
SELECT 
    log_id as id,
    request_payload->>'prompt' as user_prompt,
    response_payload->>'text' as llm_response,
    request_payload->>'context' as context_data,
    model_type as model_name,
    endpoint_name as feature_name,
    user_id,
    created_at
FROM api_logs
WHERE endpoint_name LIKE '%llm%'
  AND created_at >= NOW() - INTERVAL '7 days'
ORDER BY created_at DESC
LIMIT 50
"""
```

### Example 2: If data is in JSON columns

```python
query = """
SELECT 
    id,
    metadata->>'user_input' as user_prompt,
    metadata->>'ai_response' as llm_response,
    metadata->>'context' as context_data,
    'gpt-4' as model_name,
    feature_type as feature_name,
    user_id,
    timestamp as created_at
FROM ai_interactions
WHERE timestamp >= NOW() - INTERVAL '7 days'
ORDER BY timestamp DESC
LIMIT 50
"""
```

### Example 3: If data is across multiple tables

```python
query = """
SELECT 
    c.id,
    c.user_message as user_prompt,
    c.assistant_message as llm_response,
    c.context_json as context_data,
    m.model_name,
    f.feature_name,
    c.user_id,
    c.created_at
FROM conversations c
JOIN models m ON c.model_id = m.id
JOIN features f ON c.feature_id = f.id
WHERE c.created_at >= NOW() - INTERVAL '7 days'
ORDER BY c.created_at DESC
LIMIT 50
"""
```

---

## 🔍 Finding Your LLM Data

Don't know where your LLM data is stored? Run these queries:

### Find tables with "llm", "ai", "conversation", "chat" in the name:

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND (
    table_name LIKE '%llm%' 
    OR table_name LIKE '%ai%'
    OR table_name LIKE '%conversation%'
    OR table_name LIKE '%chat%'
    OR table_name LIKE '%prompt%'
  );
```

### Find columns that might contain prompts/responses:

```sql
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND (
    column_name LIKE '%prompt%'
    OR column_name LIKE '%response%'
    OR column_name LIKE '%message%'
    OR column_name LIKE '%llm%'
    OR column_name LIKE '%ai%'
  )
ORDER BY table_name, column_name;
```

---

## 🔄 Workflow

### Daily Review Workflow:

1. **Morning**: Load new conversations
```bash
python load_from_postgres.py
```

2. **Throughout day**: Review in UI
```bash
streamlit run human_review_app.py
```

3. **End of day**: Sync reviews to database
```bash
python save_reviews_to_db.py
```

### Automated Workflow (cron job):

```bash
# Add to crontab (runs every 6 hours)
0 */6 * * * cd /path/to/eval-tool && python load_from_postgres.py
```

---

## 💡 Tips

### Filtering Data

Only load data you want to review:

```python
# Only budget-related features
query = """
SELECT * FROM llm_conversations
WHERE feature_name IN ('budget_analysis', 'budget_forecast', 'variance_report')
LIMIT 50
"""

# Only from specific users
query = """
SELECT * FROM llm_conversations
WHERE user_id IN (SELECT id FROM users WHERE role = 'power_user')
LIMIT 50
"""

# Only long responses (might be more interesting)
query = """
SELECT * FROM llm_conversations
WHERE LENGTH(llm_response) > 500
LIMIT 50
"""

# Random sampling
query = """
SELECT * FROM llm_conversations
WHERE created_at >= NOW() - INTERVAL '7 days'
ORDER BY RANDOM()
LIMIT 50
"""
```

### Performance

For large datasets:

```python
# Use cursor pagination for large loads
def load_in_batches(batch_size=100):
    offset = 0
    while True:
        query = f"""
        SELECT * FROM llm_conversations
        LIMIT {batch_size} OFFSET {offset}
        """
        records = loader.load_conversations(query=query)
        if not records:
            break
        
        # Process batch
        review_items = loader.format_for_review(records)
        loader.save_to_pending_reviews(review_items)
        
        offset += batch_size
```

---

## 🚨 Troubleshooting

### Connection errors

```bash
# Test connection
python -c "import psycopg2; conn = psycopg2.connect('YOUR_CONNECTION_STRING'); print('✓ Connected!')"
```

### Can't find your data

Use the SQL queries above to explore your schema, or ask your DBA:
- "Where do we store LLM/AI conversation data?"
- "What table has user prompts and AI responses?"

### No data loading

Check:
1. Your query is valid SQL
2. Date filters aren't too restrictive
3. Table/column names match exactly (case sensitive)

---

## 📈 Analytics Queries

Once you have reviews in the database:

### Get acceptance rate by feature:

```sql
SELECT 
    feature,
    COUNT(*) as total_reviews,
    SUM(CASE WHEN acceptable THEN 1 ELSE 0 END) as acceptable_count,
    ROUND(100.0 * SUM(CASE WHEN acceptable THEN 1 ELSE 0 END) / COUNT(*), 2) as acceptance_rate
FROM llm_human_reviews
GROUP BY feature
ORDER BY acceptance_rate DESC;
```

### Find problematic responses:

```sql
SELECT 
    prompt,
    response,
    notes,
    tags
FROM llm_human_reviews
WHERE acceptable = false
ORDER BY timestamp DESC
LIMIT 20;
```

### Track improvement over time:

```sql
SELECT 
    DATE(timestamp) as review_date,
    COUNT(*) as reviews,
    ROUND(100.0 * SUM(CASE WHEN acceptable THEN 1 ELSE 0 END) / COUNT(*), 2) as acceptance_rate
FROM llm_human_reviews
GROUP BY DATE(timestamp)
ORDER BY review_date DESC;
```

---

## Next Steps

1. ✅ Set up Postgres connection in `.env`
2. ✅ Customize query in `load_from_postgres.py`
3. ✅ Run `python load_from_postgres.py`
4. ✅ Start reviewing in the UI
5. ✅ Sync reviews back with `python save_reviews_to_db.py`
6. ✅ Set up automated loading (cron/scheduler)

Questions? Check the examples above or dive into the code!

