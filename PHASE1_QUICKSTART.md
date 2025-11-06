# Phase 1 Quick Start: Load Existing Data

Get your existing LLM data from Postgres into the review tool.

## 🎯 Goal

Load past LLM conversations from your Postgres database so you can start reviewing them immediately - **no app changes needed**.

---

## ⚡ Quick Start (15 minutes)

### Step 1: Set Up Postgres Connection (2 min)

Create/edit `.env` file:

```bash
# Add your OpenGov Postgres connection string:
POSTGRES_URL=postgresql://username:password@host:port/database

# Example:
# POSTGRES_URL=postgresql://readonly_user:pass123@opengov-prod.us-west-2.rds.amazonaws.com:5432/opengov
```

**Tips:**
- Use a **read-only user** if possible (safer)
- Get connection details from your DBA or AWS RDS console
- Test the connection string works

### Step 2: Install Postgres Driver (1 min)

```bash
pip install psycopg2-binary
```

### Step 3: Discover Your Data (5 min)

```bash
python discover_postgres_data.py
```

This will:
- ✓ Find tables with LLM/AI data
- ✓ Show you the schema
- ✓ Display sample rows
- ✓ Generate a SQL query for you

**Follow the prompts:**
1. It'll list tables that might have LLM data
2. Pick the most likely one
3. Review the sample data
4. It'll create a custom query in `queries/` folder

### Step 4: Customize the Query (3 min)

Edit the generated query in `queries/your_table_query.sql`

Then copy it into `load_from_postgres.py` around line 40:

```python
query = """
YOUR CUSTOM QUERY HERE
"""
```

### Step 5: Load the Data (1 min)

```bash
python load_from_postgres.py
```

This loads the data into `review_data/pending_reviews.json`

### Step 6: Start Reviewing! (∞ min)

```bash
streamlit run human_review_app.py
```

Open http://localhost:8069 and start reviewing!

---

## 🔍 What If Discovery Doesn't Find Anything?

### Option 1: Ask Your Team

"Hey team, where do we store LLM/AI conversation data in Postgres?"

Common answers:
- "In the `api_logs` table"
- "In the `audit_trail` table with type='ai'"
- "We don't, it's in a separate service"
- "In the `conversations` table"

### Option 2: Manual Exploration

Connect to your database and run:

```sql
-- List all tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name;

-- Look at a specific table structure
\d your_table_name

-- or
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'your_table_name';

-- Sample some data
SELECT * FROM your_table_name LIMIT 3;
```

### Option 3: Check Application Logs

If LLM data isn't in Postgres, it might be in:
- CloudWatch logs
- DataDog
- Application log files
- A separate MongoDB/Redis
- External service (like a logging platform)

---

## 💡 Common Data Patterns

### Pattern 1: Dedicated AI Table

```sql
-- Table: llm_conversations or ai_requests
SELECT 
    id,
    user_prompt,
    ai_response,
    model_name,
    created_at
FROM llm_conversations
LIMIT 50;
```

### Pattern 2: Generic Logs Table

```sql
-- Table: api_logs or audit_logs
SELECT 
    id,
    request_data->>'prompt' as prompt,
    response_data->>'text' as response,
    endpoint,
    created_at
FROM api_logs
WHERE endpoint LIKE '%ai%' 
   OR endpoint LIKE '%llm%'
LIMIT 50;
```

### Pattern 3: Feature-Specific Tables

```sql
-- Table: budget_analyses (with AI-generated content)
SELECT 
    id,
    user_query as prompt,
    ai_analysis as response,
    'budget_analysis' as feature,
    created_at
FROM budget_analyses
WHERE ai_analysis IS NOT NULL
LIMIT 50;
```

### Pattern 4: JSON Metadata Column

```sql
-- Table: events with JSON metadata
SELECT 
    id,
    metadata->>'user_input' as prompt,
    metadata->>'ai_output' as response,
    event_type as feature,
    created_at
FROM events
WHERE event_type = 'ai_interaction'
LIMIT 50;
```

---

## 🛠️ Troubleshooting

### "POSTGRES_URL not found"

Make sure `.env` file exists in the eval-tool directory with:
```bash
POSTGRES_URL=postgresql://...
```

### "Connection refused"

- Check host/port are correct
- Verify your IP is whitelisted (for AWS RDS)
- Check VPN connection if required
- Verify firewall rules

### "Permission denied"

Your user needs at least `SELECT` permission on the tables.

### "No tables found"

Your LLM data might not be in Postgres. Check:
1. Different database
2. Different schema (not 'public')
3. Application logs instead
4. External service

### "Discovery tool found wrong tables"

Manually specify tables to check:

```python
# In discover_postgres_data.py, modify:
tables = ['your_table_1', 'your_table_2', 'your_table_3']
```

---

## 📊 What to Expect

After loading data, you'll have:

```
review_data/
  └── pending_reviews.json  (50+ items ready to review)
```

Each item contains:
- User prompt/query
- LLM response
- Context (if available)
- Model used
- Feature name
- Timestamp

---

## ✅ Success Criteria

You know Phase 1 worked when:

1. ✓ `python discover_postgres_data.py` shows your data
2. ✓ `python load_from_postgres.py` runs without errors
3. ✓ `review_data/pending_reviews.json` has items
4. ✓ Streamlit UI shows conversations to review
5. ✓ Reviews save to `review_data/reviews.json`

---

## 🎯 Next Steps After Phase 1

Once you've reviewed some data:

1. **Analyze patterns**: What's failing? What's good?
2. **Export training data**: Use high-quality examples
3. **Track metrics**: Acceptance rate by feature
4. **Move to Phase 2**: Real-time capture (when ready for PR)

---

## 🆘 Still Stuck?

Common scenarios:

**"I can't find the LLM data"**
→ It might not be in Postgres. Check application logs, CloudWatch, or ask the team.

**"Data is spread across many tables"**
→ Write a JOIN query to combine them. The discovery tool generates a starting point.

**"Data format doesn't match what the tool expects"**
→ Edit `load_from_postgres.py` around line 85 to map your columns correctly.

**"I have millions of rows"**
→ Start with LIMIT 100, add WHERE filters (date range, specific features, etc.)

---

## 📝 Example End-to-End

```bash
# 1. Set up connection
echo 'POSTGRES_URL=postgresql://user:pass@host:5432/db' > .env

# 2. Discover data
python discover_postgres_data.py
# → Pick table #3 (api_logs)
# → Reviews schema and samples
# → Generates query

# 3. Edit the query in load_from_postgres.py
# (customize column mappings)

# 4. Load data
python load_from_postgres.py
# ✓ Loaded 50 records

# 5. Review in UI
streamlit run human_review_app.py
# → Start reviewing at localhost:8069

# 6. Reviews saved automatically to JSON
# → Can export to CSV or sync to DB later
```

**Total time**: 15-30 minutes depending on data discovery

---

## 💪 You've Got This!

Phase 1 is the foundation. Once you can see your data in the review UI, everything else falls into place.

**Pro tip**: Start with just 10-20 reviews to test the workflow before loading thousands.

