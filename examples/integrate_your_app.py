"""
Example: Integrating with your own application

This shows how to create a custom connector for your specific use case.
"""

from typing import Any
from eval_framework import BaseConnector, TestRunner, TestCase, ResultsManager


class MyAppConnector(BaseConnector):
    """
    Custom connector for your application
    
    Replace this implementation with calls to your actual system!
    """
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        # Initialize your app connection here
        # e.g., self.client = YourAppClient(api_key=...)
    
    def call(self, input_data: Any, **kwargs) -> str:
        """
        Call your application and return the result
        
        Examples of what you might do here:
        - Call a REST API
        - Execute a CLI command
        - Call a local function/library
        - Query a database
        - Interact with a gRPC service
        """
        
        # Example 1: CLI Command
        # import subprocess
        # result = subprocess.run(['your-app', 'process', input_data], capture_output=True, text=True)
        # return result.stdout
        
        # Example 2: REST API
        # import requests
        # response = requests.post('http://your-api.com/process', json={'input': input_data})
        # return response.json()['output']
        
        # Example 3: Direct function call
        # from your_app import process_input
        # return process_input(input_data)
        
        # For this example, we'll just return a mock response
        return f"Processed by MyApp: {input_data}"


def main():
    """
    Example: Running tests against your application
    """
    
    # 1. Create your custom connector
    my_app = MyAppConnector(config={
        'api_url': 'http://localhost:8000',
        'timeout': 30
    })
    
    # 2. Define test cases specific to your app
    test_cases = [
        TestCase(
            name="Data validation",
            input='{"user_id": 123, "action": "login"}',
            evaluators=[
                {"type": "contains", "value": "Processed"},
                {"type": "contains", "value": "MyApp"}
            ],
            metadata={
                "feature": "authentication",
                "priority": "high"
            }
        ),
        TestCase(
            name="Error handling",
            input="invalid_input!!!",
            evaluators=[
                {"type": "length", "min_length": 1}  # Should still return something
            ],
            metadata={
                "feature": "error_handling",
                "priority": "medium"
            }
        ),
        TestCase(
            name="Complex query",
            input="SELECT * FROM users WHERE id > 100",
            evaluators=[
                {"type": "contains", "value": "Processed"},
                {"type": "regex", "pattern": "Processed.*SELECT"}
            ],
            metadata={
                "feature": "query_processing",
                "priority": "high"
            }
        ),
    ]
    
    # 3. Run tests
    runner = TestRunner(my_app, verbose=True)
    results = runner.run_suite(test_cases, suite_name="MyApp Integration Tests")
    
    # 4. Save and analyze results
    results_mgr = ResultsManager()
    output_file = results_mgr.save_results(results)
    results_mgr.print_summary(results)
    
    print(f"\n✓ Results saved to: {output_file}")
    
    # 5. You can also filter/analyze by metadata
    print("\n=== High Priority Tests ===")
    high_priority = [r for r in results.test_results if r.metadata.get('priority') == 'high']
    for result in high_priority:
        status = "✓" if result.passed else "✗"
        print(f"{status} {result.test_name}: {result.overall_score:.2f}")


if __name__ == '__main__':
    main()

