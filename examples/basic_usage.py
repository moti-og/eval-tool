"""
Basic usage example: Running evaluations programmatically
"""

from eval_framework import (
    TestRunner,
    TestCase,
    ResultsManager,
    MockConnector
)


def main():
    # 1. Create a connector (using mock for this example)
    connector = MockConnector(response="This is a test response")
    
    # 2. Define test cases
    test_cases = [
        TestCase(
            name="Test 1: Basic check",
            input="Hello world",
            evaluators=[
                {"type": "contains", "value": "test"},
                {"type": "length", "min_length": 10}
            ]
        ),
        TestCase(
            name="Test 2: Exact match",
            input="What is AI?",
            expected_output="This is a test response: What is AI?",
            evaluators=[
                {"type": "exact_match"}
            ]
        ),
    ]
    
    # 3. Create test runner
    runner = TestRunner(connector, verbose=True)
    
    # 4. Run tests
    results = runner.run_suite(test_cases, suite_name="My Test Suite")
    
    # 5. Save and display results
    results_mgr = ResultsManager()
    results_mgr.save_results(results)
    results_mgr.print_summary(results)
    
    # 6. Access results programmatically
    print("\n=== Programmatic Access ===")
    for test_result in results.test_results:
        print(f"{test_result.test_name}: {'PASS' if test_result.passed else 'FAIL'}")
        print(f"  Score: {test_result.overall_score:.2f}")


if __name__ == '__main__':
    main()

