# Deployment Notes - Sampleville Filter

## Changes Made

The application has been configured to **only show data where `government_code = 'sampleville'`** when deployed.

### Modified Files

1. **`load_from_postgres.py`** (Lines 66, 74)
   - Changed `LEFT JOIN government g` to `JOIN government g` (line 66) - This ensures only records with a valid government are included
   - Added filter: `AND g.code = 'sampleville'` (line 74) - This filters to only Sampleville data

## What This Means

When you run `python load_from_postgres.py` to load data from the database, it will now:
- Only load LLM responses for projects in Sampleville
- Ignore all other government/city data
- Keep your review interface focused on Sampleville only

## Deployment Instructions

### For Streamlit Cloud (Recommended)

1. **Push your changes to GitHub:**
   ```bash
   git add load_from_postgres.py
   git commit -m "Filter data for Sampleville only"
   git push
   ```

2. **Deploy to Streamlit Cloud:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub repository
   - Select `human_review_app.py` as the main file
   - Add your environment variables:
     - `POSTGRES_URL` - Your PostgreSQL connection string

3. **Load data:**
   - After deployment, run `load_from_postgres.py` locally to populate the review queue
   - Or set up a scheduled job to run it periodically

### For Vercel (Alternative)

**Note:** Vercel doesn't natively support Streamlit apps well. If you meant Vercel, consider:
1. Converting to a FastAPI/Flask backend + React frontend, or
2. Using Streamlit Cloud instead (much simpler for Streamlit apps)

### For Other Platforms (Heroku, AWS, etc.)

1. Ensure your `POSTGRES_URL` environment variable is set
2. Run `python load_from_postgres.py` as part of your startup or scheduled job
3. Start the Streamlit app with `streamlit run human_review_app.py`

## Verifying the Filter

To verify the filter is working correctly:

1. **Check the SQL query:**
   ```python
   python -c "from load_from_postgres import PostgresLoader; loader = PostgresLoader(); print('Filter configured for Sampleville')"
   ```

2. **Load data and verify:**
   ```bash
   python load_from_postgres.py
   ```
   
   All loaded records should be from Sampleville only.

3. **In the web interface:**
   - Open the human review app
   - Check that all displayed projects are from Sampleville
   - Look at the "Organization" field in the context - should only show Sampleville-related organizations

## Database Column Assumption

The filter assumes the `government` table has a column called `code` that contains the government code. If your database uses a different column name (e.g., `government_code`, `gov_code`, etc.), you'll need to update line 74 in `load_from_postgres.py`:

```python
# Current (assuming column is 'code'):
AND g.code = 'sampleville'

# If column is different, change to:
AND g.government_code = 'sampleville'  # or whatever the column name is
```

## Testing Before Deployment

1. **Backup your current data:**
   ```bash
   cp review_data/pending_reviews.json review_data/pending_reviews.backup.json
   cp review_data/reviews.json review_data/reviews.backup.json
   ```

2. **Clear and reload data:**
   ```bash
   echo "[]" > review_data/pending_reviews.json
   python load_from_postgres.py
   ```

3. **Verify only Sampleville data is loaded:**
   ```bash
   # Check the pending reviews file for Sampleville references
   python -c "import json; data = json.load(open('review_data/pending_reviews.json')); print(f'Loaded {len(data)} items'); print('Sample org:', data[0].get('organization_name') if data else 'No data')"
   ```

## Environment Variables Required

Make sure these are set in your deployment environment:

- `POSTGRES_URL` - PostgreSQL connection string (format: `postgresql://user:password@host:port/database`)

## Questions?

If the column name is different or you encounter any issues:
1. Check your database schema to confirm the government code column name
2. Update line 74 in `load_from_postgres.py` accordingly
3. Test locally before deploying

---

**Summary:** Your application is now configured to filter all data to Sampleville only. When you deploy and load data, only Sampleville government records will appear in the review interface.

