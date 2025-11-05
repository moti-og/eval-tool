# Integration Guide: Connecting Your Application

This guide shows you exactly how to integrate the eval tool with your application.

## Overview

There are three main ways to integrate:

1. **Modify the built-in CustomAppConnector** (quickest)
2. **Create a new connector class** (more flexible)
3. **Use the framework programmatically** (most control)

## Method 1: Modify CustomAppConnector (Recommended for MVP)

Edit `eval_framework/connectors.py` and find the `CustomAppConnector.call()` method:

### For REST APIs

```python
def call(self, input_data: Any, endpoint: str = "/api/process", **kwargs) -> str:
    headers = {"Authorization": f"Bearer {self.api_key}"}
    
    response = requests.post(
        f"{self.api_url}{endpoint}",
        json={"input": input_data, **kwargs},
        headers=headers,
        timeout=30
    )
    response.raise_for_status()
    return response.json().get("output", response.text)
```

### For CLI Tools

```python
def call(self, input_data: Any, **kwargs) -> str:
    import subprocess
    
    result = subprocess.run(
        ['your-cli-tool', 'process', str(input_data)],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        raise Exception(f"CLI error: {result.stderr}")
    
    return result.stdout
```

### For Python Libraries/Functions

```python
def call(self, input_data: Any, **kwargs) -> str:
    from your_app import process_data
    
    result = process_data(input_data, **kwargs)
    return str(result)
```

### For gRPC Services

```python
def call(self, input_data: Any, **kwargs) -> str:
    import grpc
    from your_app import your_service_pb2, your_service_pb2_grpc
    
    with grpc.insecure_channel(self.api_url) as channel:
        stub = your_service_pb2_grpc.YourServiceStub(channel)
        request = your_service_pb2.Request(input=input_data)
        response = stub.Process(request)
        return response.output
```

## Method 2: Create a New Connector Class

Create a file `my_connector.py`:

```python
from eval_framework import BaseConnector
from typing import Any

class MyAppConnector(BaseConnector):
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        # Initialize your client
        self.client = YourAppClient(api_key, base_url)
    
    def call(self, input_data: Any, **kwargs) -> str:
        # Call your application
        response = self.client.process(input_data)
        return response.result
```

Use it:

```python
from my_connector import MyAppConnector
from eval_framework import TestRunner, TestCase

connector = MyAppConnector(
    api_key="your_key",
    base_url="https://api.yourapp.com"
)

runner = TestRunner(connector)
results = runner.run_suite(test_cases)
```

## Method 3: Full Programmatic Control

See `examples/integrate_your_app.py` for a complete example.

## Real-World Integration Examples

### Example 1: OpenGov Budget Application

```python
from eval_framework import BaseConnector
import requests

class OpenGovBudgetConnector(BaseConnector):
    def __init__(self, api_key: str, environment: str = "staging"):
        self.api_key = api_key
        self.base_url = f"https://{environment}.opengov.com/api/v1"
    
    def call(self, input_data: Any, **kwargs) -> str:
        # input_data could be a budget query or analysis request
        endpoint = kwargs.get('endpoint', '/budget/analyze')
        
        response = requests.post(
            f"{self.base_url}{endpoint}",
            json={
                "query": input_data,
                "options": kwargs
            },
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        response.raise_for_status()
        return response.json().get('analysis', '')

# Test cases for budget application
test_cases = [
    TestCase(
        name="Budget variance analysis",
        input="Calculate variance for Q1 2024",
        evaluators=[
            {"type": "json_schema"},
            {"type": "contains", "value": "variance"},
            {"type": "contains", "value": "Q1"}
        ]
    ),
    TestCase(
        name="Budget forecast",
        input="Forecast spending for next quarter",
        evaluators=[
            {"type": "contains", "value": "forecast"},
            {"type": "regex", "pattern": "\\$[0-9,]+"}
        ]
    )
]
```

### Example 2: LLM-Powered Document Analysis

```python
from eval_framework import BaseConnector, OpenAIConnector

class DocumentAnalyzerConnector(BaseConnector):
    def __init__(self, openai_key: str):
        self.llm = OpenAIConnector(api_key=openai_key, model="gpt-4")
        self.system_prompt = """
        You are a document analyzer. Extract key information and provide summaries.
        Always respond in JSON format with: summary, key_points, sentiment.
        """
    
    def call(self, input_data: Any, **kwargs) -> str:
        # input_data is the document text
        return self.llm.call(
            input_data,
            system_prompt=self.system_prompt,
            **kwargs
        )

# Test cases
test_cases = [
    TestCase(
        name="Extract key points",
        input="[Long document text here...]",
        evaluators=[
            {"type": "json_schema", "schema": {"required": ["summary", "key_points", "sentiment"]}},
            {"type": "length", "min_length": 50}
        ]
    )
]
```

### Example 3: SQL Query Generator

```python
from eval_framework import BaseConnector

class SQLGeneratorConnector(BaseConnector):
    def __init__(self, db_connection_string: str):
        import sqlalchemy
        self.engine = sqlalchemy.create_engine(db_connection_string)
        self.llm = OpenAIConnector()  # To generate SQL
    
    def call(self, input_data: Any, **kwargs) -> str:
        # input_data is natural language query
        
        # Step 1: Generate SQL using LLM
        sql_query = self.llm.call(
            f"Convert to SQL: {input_data}\nDatabase schema: {self.get_schema()}"
        )
        
        # Step 2: Validate and execute
        try:
            with self.engine.connect() as conn:
                result = conn.execute(sql_query)
                return str(result.fetchall())
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_schema(self):
        # Return your database schema
        return "..."

# Test cases
test_cases = [
    TestCase(
        name="Simple SELECT query",
        input="Get all users from California",
        evaluators=[
            {"type": "regex", "pattern": "SELECT.*FROM.*users"},
            {"type": "contains", "value": "California"}
        ]
    )
]
```

## Handling Different Input/Output Types

### JSON Input/Output

```python
import json

class JSONAPIConnector(BaseConnector):
    def call(self, input_data: Any, **kwargs) -> str:
        # Parse input if it's a string
        if isinstance(input_data, str):
            try:
                input_json = json.loads(input_data)
            except json.JSONDecodeError:
                input_json = {"text": input_data}
        else:
            input_json = input_data
        
        # Call your API
        response = your_api.process(input_json)
        
        # Return as JSON string
        return json.dumps(response)
```

### File-Based Input

```python
class FileProcessorConnector(BaseConnector):
    def call(self, input_data: Any, **kwargs) -> str:
        # input_data is a file path
        from pathlib import Path
        
        file_path = Path(input_data)
        if not file_path.exists():
            return f"Error: File not found: {input_data}"
        
        # Process the file
        result = your_app.process_file(file_path)
        return str(result)
```

### Streaming Responses

```python
class StreamingConnector(BaseConnector):
    def call(self, input_data: Any, **kwargs) -> str:
        # Collect streaming response
        chunks = []
        
        for chunk in your_app.stream_process(input_data):
            chunks.append(chunk)
        
        return "".join(chunks)
```

## Advanced: Custom Evaluators for Your Domain

```python
def check_budget_format(output: str, expected: str = None, **kwargs) -> dict:
    """
    Custom evaluator for budget outputs
    """
    import re
    
    # Check if output contains dollar amounts
    amounts = re.findall(r'\$[\d,]+\.?\d*', output)
    
    # Check if output has required sections
    required_sections = ['Summary', 'Details', 'Total']
    has_sections = sum(1 for section in required_sections if section in output)
    
    score = (len(amounts) > 0) * 0.5 + (has_sections / len(required_sections)) * 0.5
    
    return {
        "passed": score >= 0.8,
        "score": score,
        "details": {
            "amounts_found": len(amounts),
            "sections_found": has_sections,
            "required_sections": len(required_sections)
        }
    }

# Use in test cases
test_cases = [
    TestCase(
        name="Budget report format",
        input="Generate budget report",
        evaluators=[
            {"type": "custom", "function": "check_budget_format"}
        ]
    )
]

# Pass to runner
custom_evaluators = {"check_budget_format": check_budget_format}
runner = TestRunner(connector, custom_evaluators=custom_evaluators)
```

## Testing Strategy

### 1. Start Simple

```yaml
# test_cases/smoke_test.yaml
name: "Smoke Tests"
test_cases:
  - name: "App is responsive"
    input: "ping"
    evaluators:
      - type: "length"
        min_length: 1
```

### 2. Add Functional Tests

```yaml
# test_cases/functional.yaml
name: "Functional Tests"
test_cases:
  - name: "Core feature 1"
    input: "test core feature"
    expected_output: "expected result"
    evaluators:
      - type: "contains"
        value: "core feature"
```

### 3. Add Quality Tests

```yaml
# test_cases/quality.yaml
name: "Quality Tests"
test_cases:
  - name: "Response quality"
    input: "complex query"
    evaluators:
      - type: "semantic_similarity"
        threshold: 0.85
      - type: "length"
        min_length: 100
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/eval.yml
name: Run Evaluations

on: [push, pull_request]

jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: python run_eval.py --test-suite test_cases/smoke_test.yaml --quiet
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          APP_API_KEY: ${{ secrets.APP_API_KEY }}
```

### Jenkins

```groovy
pipeline {
    agent any
    stages {
        stage('Run Evals') {
            steps {
                sh 'pip install -r requirements.txt'
                sh 'python run_eval.py --test-suite test_cases/all.yaml'
            }
        }
    }
}
```

## Tips for Production

1. **Start with mock connector** - Get your test cases right first
2. **Use metadata** - Tag tests by feature, priority, team
3. **Keep tests fast** - Use smaller models for quick feedback
4. **Version your tests** - Track changes to test cases
5. **Monitor over time** - Compare results to track regressions
6. **Separate test suites** - Different suites for different purposes (smoke, functional, quality)

## Troubleshooting

### My app returns errors

Add error handling to your connector:

```python
def call(self, input_data: Any, **kwargs) -> str:
    try:
        return your_app.process(input_data)
    except Exception as e:
        return f"Error: {str(e)}"
```

### Tests are too slow

- Use faster models (gpt-3.5-turbo vs gpt-4)
- Run tests in parallel (future enhancement)
- Cache responses for identical inputs
- Use mock connector for test development

### Results are inconsistent

- Set temperature=0 for deterministic outputs
- Use semantic_similarity instead of exact_match
- Add multiple evaluation criteria
- Run tests multiple times and aggregate

## Next Steps

1. Clone one of the example connectors above
2. Modify it to call your application
3. Create test cases specific to your use case
4. Run and iterate!

Need help? Check the examples/ directory for more code samples.

