

# Human Review System Guide

This guide explains how to integrate human review of LLM responses into your OpenGov application.

## 🎯 Overview

The human review system lets you:
1. **Capture** LLM responses from your OpenGov app
2. **Review** them in a beautiful web interface
3. **Rate** and provide feedback
4. **Export** the feedback for fine-tuning your LLMs

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Integrate into Your OpenGov App

Add this to your OpenGov application code:

```python
from opengov_integration import capture_for_review

# After getting an LLM response:
response = your_llm.generate(prompt, context)

# Capture it for review:
capture_for_review(
    prompt=prompt,
    context=context,
    response=response,
    feature="budget_analysis",
    model="gpt-4"
)
```

### 3. Launch Review Interface

```bash
streamlit run human_review_app.py
```

### 4. Review Responses

Open browser → Review → Rate → Submit → Export feedback

## 📦 Storage Options

### Option 1: JSON (Default - Easiest)

- **Pros**: No setup, human-readable, git-friendly
- **Cons**: Not ideal for 1000s of reviews
- **Good for**: MVP, small teams, < 1000 reviews

```python
from review_storage import JSONStorage
storage = JSONStorage("review_data/reviews.json")
```

### Option 2: CSV (Spreadsheet-Friendly)

- **Pros**: Open in Excel/Google Sheets, easy analysis
- **Cons**: No nested data, harder to query
- **Good for**: Sharing with non-technical stakeholders

```python
from review_storage import CSVStorage
storage = CSVStorage("review_data/reviews.csv")
```

### Option 3: MongoDB (Production Scale)

- **Pros**: Scales to millions, fast queries, analytics
- **Cons**: Requires setup, hosting costs
- **Good for**: Production, large teams, > 1000 reviews

```python
from review_storage import MongoDBStorage

# Use MongoDB Atlas (free tier available)
storage = MongoDBStorage(
    connection_string="mongodb+srv://user:pass@cluster.mongodb.net/",
    db_name="opengov_llm_reviews"
)
```

#### MongoDB Atlas Setup (5 minutes):

1. Go to https://www.mongodb.com/cloud/atlas/register
2. Create free cluster
3. Get connection string
4. Update `human_review_app.py`:

```python
# Change this line:
STORAGE_TYPE = "mongodb"

# And add your connection string in .env:
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
```

## 🔧 Integration Patterns

### Pattern 1: Capture Everything

```python
from opengov_integration import capture_for_review

def your_feature(user_input: str):
    response = llm.generate(user_input)
    
    capture_for_review(
        prompt=user_input,
        response=response,
        feature="your_feature"
    )
    
    return response
```

### Pattern 2: Sample High-Volume Features (Recommended)

```python
from opengov_integration import capture_sample

def frequent_feature(user_input: str):
    response = llm.generate(user_input)
    
    # Only capture 10% for review
    capture_sample(
        prompt=user_input,
        response=response,
        sample_rate=0.10,
        feature="frequent_feature"
    )
    
    return response
```

### Pattern 3: Smart Capture (Most Efficient)

```python
from opengov_integration import OpenGovReviewCapture

capturer = OpenGovReviewCapture()

def smart_feature(user_input: str):
    response = llm.generate(user_input)
    
    # Only capture if potentially problematic
    if needs_review(response):
        capturer.capture(
            prompt=user_input,
            response=response,
            feature="smart_feature",
            metadata={"flagged": True}
        )
    
    return response

def needs_review(response: str) -> bool:
    # Your logic here
    error_indicators = ['error', 'unknown', 'cannot', 'unclear']
    return any(word in response.lower() for word in error_indicators)
```

### Pattern 4: Decorator (Cleanest Code)

```python
from opengov_integration import review_llm_response

@review_llm_response(feature="budget_reports", sample_rate=0.2)
def generate_budget_report(query: str, context: str) -> str:
    return llm.generate(query, context)
```

## 📊 Review Interface Features

### Main Review Page

- **Prompt**: What was sent to the LLM
- **Context**: Additional data provided
- **Response**: What the LLM returned
- **Rating**: 1-5 stars
- **Criteria**: Accuracy, Relevance, Completeness, Formatting
- **Issues**: Flag specific problems
- **Notes**: Free-form feedback
- **Tags**: Categorize for later filtering

### History Page

- View all past reviews
- Filter by rating, feature, tags
- Export as CSV or JSON
- Search and analyze

### Analytics Page

- Rating distribution
- Common issues
- Performance by feature
- Trends over time

## 💾 Exporting for Training

Export high-quality responses for LLM fine-tuning:

```python
from review_storage import JSONStorage

storage = JSONStorage()

# Export 4-5 star reviews as JSONL
storage.export_for_training("training_data.jsonl")

# Use with OpenAI fine-tuning:
# openai api fine_tunes.create -t training_data.jsonl -m gpt-3.5-turbo
```

## 🎨 Customization

### Change Rating Scale

Edit `human_review_app.py`:

```python
rating = st.select_slider(
    "Overall Rating",
    options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],  # Change to 1-10
    value=5
)
```

### Add Custom Criteria

```python
# Add your own checkboxes:
opengov_compliant = st.checkbox("✓ OpenGov Compliant")
within_budget = st.checkbox("✓ Within Budget Guidelines")
```

### Change Storage Backend

In `human_review_app.py`, change:

```python
STORAGE_TYPE = "json"  # or "csv" or "mongodb"
```

## 📈 Recommended Workflow

### Phase 1: MVP (Week 1)

1. Use JSON storage
2. Capture 100% of responses from 1-2 features
3. Have 2-3 people review daily
4. Goal: Understand common issues

### Phase 2: Scale (Weeks 2-4)

1. Add sampling (capture 10-20%)
2. Expand to more features
3. Switch to CSV or MongoDB
4. Weekly review sessions

### Phase 3: Production (Month 2+)

1. MongoDB for storage
2. Smart capture (only edge cases)
3. Regular exports for training
4. Track metrics over time

## 🔍 Best Practices

### Capture Strategy

**Do:**
- ✅ Sample high-volume features (10-20%)
- ✅ Capture 100% of new/experimental features
- ✅ Flag potential issues automatically
- ✅ Include relevant metadata

**Don't:**
- ❌ Capture every single response (too much noise)
- ❌ Forget to include context
- ❌ Skip metadata (feature, model, user)
- ❌ Let pending reviews pile up

### Review Strategy

**Do:**
- ✅ Review regularly (daily or weekly)
- ✅ Use consistent criteria
- ✅ Add detailed notes for edge cases
- ✅ Tag responses for easy filtering
- ✅ Export and analyze monthly

**Don't:**
- ❌ Rush through reviews
- ❌ Only review "bad" responses
- ❌ Skip the notes field
- ❌ Forget to export for training

## 🚨 Troubleshooting

### No pending reviews showing up

1. Check `review_data/pending_reviews.json` exists
2. Verify your OpenGov app is calling `capture_for_review()`
3. Check for errors in your app logs

### Reviews not saving

1. Check file permissions on `review_data/` directory
2. Verify storage type is configured correctly
3. Check browser console for errors

### Interface is slow

1. Switch from JSON to MongoDB
2. Archive old reviews
3. Use sampling instead of capturing everything

## 🔗 Integration with OpenGov CI/CD

### GitHub Actions

```yaml
# .github/workflows/llm-quality.yml
name: LLM Quality Check

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  check-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Check LLM quality metrics
        run: |
          python -c "
          from review_storage import JSONStorage
          storage = JSONStorage()
          reviews = storage.get_all_reviews()
          avg_rating = sum(r['rating'] for r in reviews) / len(reviews)
          if avg_rating < 3.5:
            raise Exception(f'LLM quality below threshold: {avg_rating}')
          "
```

## 📚 Example Use Cases

### Use Case 1: Budget Analysis Quality

```python
# Capture all budget analysis responses for 2 weeks
capture_for_review(
    prompt=user_query,
    response=llm_response,
    feature="budget_analysis",
    metadata={
        "department": department,
        "amount": budget_amount
    }
)

# After 2 weeks:
# - Review ratings
# - Identify common failure modes
# - Export high-quality examples
# - Fine-tune model
```

### Use Case 2: A/B Testing Models

```python
# Test GPT-4 vs Claude
if random.random() < 0.5:
    response = gpt4.generate(prompt)
    model = "gpt-4"
else:
    response = claude.generate(prompt)
    model = "claude-3"

capture_for_review(
    prompt=prompt,
    response=response,
    model=model,
    feature="ab_test"
)

# Compare ratings by model in Analytics page
```

### Use Case 3: Safety Monitoring

```python
# Capture all responses for safety review
if is_sensitive_feature(feature_name):
    capture_for_review(
        prompt=prompt,
        response=response,
        feature=feature_name,
        metadata={"requires_safety_review": True}
    )
```

## 🎯 Success Metrics

Track these metrics:

- **Coverage**: % of LLM calls being reviewed
- **Quality**: Average rating of reviewed responses
- **Consistency**: Inter-rater reliability
- **Actionability**: % of reviews leading to improvements
- **Velocity**: Time from capture to review

## Next Steps

1. ✅ Add `capture_for_review()` to your first OpenGov feature
2. ✅ Run `streamlit run human_review_app.py`
3. ✅ Review 10-20 responses
4. ✅ Export feedback
5. ✅ Iterate and improve!

---

**Questions?** Check the `examples/opengov_integration_example.py` file for complete code samples.

