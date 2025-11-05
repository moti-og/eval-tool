# Quick Start Guide

Get your evaluation framework running in 5 minutes!

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Test with Mock Connector

Run the example test suite (no API keys needed):

```bash
python run_eval.py --test-suite test_cases/example.yaml
```

You should see output like:
```
Running test suite: Example Test Suite
Total tests: 5

[1/5] Running: Simple exact match test...
  ✓ PASSED (score: 1.00, time: 0.00s)
...
```

## Step 3: Set Up Your Environment

Create a `.env` file (copy from `.env.example`):

```bash
# For OpenAI
OPENAI_API_KEY=sk-...

# For Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# For your custom app
APP_API_URL=http://localhost:8000
APP_API_KEY=your_key
```

## Step 4: Test with Real LLMs

Run with OpenAI:
```bash
python run_eval.py --test-suite test_cases/llm_example.yaml --connector openai --model gpt-4
```

Run with Anthropic:
```bash
python run_eval.py --test-suite test_cases/llm_example.yaml --connector anthropic
```

## Step 5: Integrate Your Application

### Option A: Use the Custom Connector

Edit `eval_framework/connectors.py` and modify the `CustomAppConnector.call()` method to call your application.

Then run:
```bash
python run_eval.py --test-suite test_cases/custom_app_example.yaml --connector custom_app
```

### Option B: Create Your Own Connector

See `examples/integrate_your_app.py` for a complete example:

```python
from eval_framework import BaseConnector, TestRunner, TestCase

class MyAppConnector(BaseConnector):
    def call(self, input_data, **kwargs):
        # Call your app here
        return your_app.process(input_data)

# Use it
connector = MyAppConnector()
runner = TestRunner(connector)
results = runner.run_suite(test_cases)
```

## Common Use Cases

### Create Your Own Test Suite

Create a YAML file in `test_cases/`:

```yaml
name: "My Test Suite"
description: "Testing my application"

test_cases:
  - name: "Test 1"
    input: "test input"
    expected_output: "expected result"
    evaluators:
      - type: "exact_match"
      - type: "contains"
        value: "keyword"
```

### Compare Different Models

```bash
# Run tests with GPT-3.5
python run_eval.py --test-suite test_cases/llm_example.yaml --connector openai --model gpt-3.5-turbo --output gpt35_results.json

# Run tests with GPT-4
python run_eval.py --test-suite test_cases/llm_example.yaml --connector openai --model gpt-4 --output gpt4_results.json

# Compare
python compare_results.py gpt35_results.json gpt4_results.json
```

### Use Custom Evaluators

```python
def my_custom_check(output, expected=None, **kwargs):
    # Your logic here
    return {"passed": True, "score": 0.95}

custom_evaluators = {"my_check": my_custom_check}
runner = TestRunner(connector, custom_evaluators=custom_evaluators)
```

## Available Evaluators

- `exact_match` - Exact string matching
- `contains` - Check if output contains text
- `regex` - Regular expression matching
- `semantic_similarity` - Semantic similarity using embeddings
- `json_schema` - Validate JSON structure
- `length` - Check length constraints
- `custom` - Your custom function

## Examples

The `examples/` directory contains:

- `basic_usage.py` - Simple programmatic usage
- `custom_evaluator.py` - Creating custom evaluators
- `integrate_your_app.py` - Integrating with your application
- `compare_models.py` - Comparing multiple models/systems

Run any example:
```bash
python examples/basic_usage.py
```

## Results

Results are saved in `results/` as JSON files with timestamps. They include:
- All test inputs and outputs
- Evaluation scores and pass/fail status
- Execution times
- Metadata

View results:
```bash
cat results/your_test_20241105_143022.json
```

## Next Steps

1. **Define your test cases** - Create YAML files for your specific use cases
2. **Connect to your app** - Modify `CustomAppConnector` or create your own
3. **Add custom evaluators** - Write validators specific to your domain
4. **Run regularly** - Set up CI/CD to run evals on every deploy
5. **Track over time** - Compare results to track improvements/regressions

## Tips

- Start with simple evaluators (`contains`, `exact_match`)
- Use metadata to organize tests by feature/priority
- Run in `--quiet` mode in CI/CD
- Use semantic similarity for flexible matching
- Create separate test suites for different aspects (quality, safety, performance)

## Need Help?

- See `README.md` for detailed documentation
- Check `examples/` for code samples
- Look at `test_cases/` for YAML examples

