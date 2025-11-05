# LLM Evaluation Tool

A comprehensive evaluation framework for testing LLM applications with both **automated testing** and **human review capabilities**.

## 🎯 Two Modes of Operation

### 1. Automated Evaluation
Run automated tests with various evaluators (exact match, semantic similarity, regex, etc.)
- Command-line interface
- YAML test definitions
- Multiple connectors (OpenAI, Anthropic, custom APIs)
- Results tracking and comparison

### 2. Human Review Interface 
Beautiful web UI for human evaluation of LLM responses
- Review prompt, context, and responses
- Rate and provide feedback
- Export feedback for LLM fine-tuning
- Multiple storage options (JSON, CSV, MongoDB)

## Quick Start

### Automated Testing

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run example tests:
```bash
python run_eval.py --test-suite test_cases/example.yaml
```

3. Test with real LLMs (set API keys in `.env`):
```bash
python run_eval.py --test-suite test_cases/llm_example.yaml --connector openai
```

### Human Review Interface

1. Install dependencies (if not already done):
```bash
pip install -r requirements.txt
```

2. Launch the review interface:
```bash
streamlit run human_review_app.py
```

3. Integrate into your application:
```python
from opengov_integration import capture_for_review

# After getting LLM response:
capture_for_review(
    prompt=user_input,
    response=llm_response,
    feature="your_feature"
)
```

See **[HUMAN_REVIEW_GUIDE.md](HUMAN_REVIEW_GUIDE.md)** for complete integration guide.

## Structure

- `run_eval.py` - Main CLI entry point
- `eval_framework/` - Core evaluation framework
  - `runners.py` - Test execution logic
  - `evaluators.py` - Scoring and validation logic
  - `connectors.py` - Connect to your application/LLM
  - `results.py` - Results storage and reporting
- `test_cases/` - YAML test case definitions
- `results/` - Evaluation results (JSON with timestamps)

## Test Case Format

```yaml
name: "Example Test Suite"
description: "Tests for my application"

test_cases:
  - name: "Test 1"
    input: "User prompt or data"
    expected_output: "Expected result"
    evaluators:
      - type: "exact_match"
      - type: "contains"
        value: "important keyword"
    
  - name: "Test 2"
    input: "Another test"
    evaluators:
      - type: "semantic_similarity"
        threshold: 0.85
      - type: "custom"
        function: "my_custom_validator"
```

## Evaluation Types

- `exact_match` - Exact string matching
- `contains` - Check if output contains specific text
- `regex` - Regular expression matching
- `semantic_similarity` - Semantic similarity using embeddings
- `json_schema` - Validate JSON structure
- `custom` - Your custom validation function

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Get running in 5 minutes
- **[HUMAN_REVIEW_GUIDE.md](HUMAN_REVIEW_GUIDE.md)** - Human evaluation system (for OpenGov integration)
- **[INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)** - Connect to your application
- **examples/** - Code samples for different use cases

## Connecting to Your Application

### For Automated Testing

Edit `eval_framework/connectors.py` to integrate with your actual application:

```python
class MyAppConnector(BaseConnector):
    def call(self, input_data):
        # Call your API, CLI tool, or LLM here
        response = your_app.process(input_data)
        return response
```

### For Human Review

Add to your OpenGov application:

```python
from opengov_integration import capture_for_review

# After getting LLM response:
response = your_llm.generate(prompt, context)

capture_for_review(
    prompt=prompt,
    context=context,
    response=response,
    feature="budget_analysis",
    model="gpt-4"
)
```

Then launch review interface:
```bash
streamlit run human_review_app.py
```

