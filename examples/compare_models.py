"""
Example: Comparing different models or configurations

This shows how to run the same tests against multiple systems and compare results.
"""

import os
from eval_framework import (
    TestRunner,
    TestCase,
    ResultsManager,
    OpenAIConnector,
    MockConnector
)


def create_test_cases():
    """Define common test cases"""
    return [
        TestCase(
            name="Simple question",
            input="What is 2+2?",
            evaluators=[
                {"type": "contains", "value": "4"}
            ]
        ),
        TestCase(
            name="Code generation",
            input="Write a Python function to check if a number is even",
            evaluators=[
                {"type": "contains", "value": "def"},
                {"type": "contains", "value": "even"},
                {"type": "regex", "pattern": "%.*2"}
            ]
        ),
        TestCase(
            name="Reasoning",
            input="If all roses are flowers and some flowers fade quickly, can we conclude that some roses fade quickly?",
            evaluators=[
                {"type": "contains", "value": "no"},
                {"type": "length", "min_length": 20}
            ]
        ),
    ]


def main():
    """
    Compare multiple models/systems
    """
    
    # Check if API key is available
    has_openai = bool(os.getenv('OPENAI_API_KEY'))
    
    test_cases = create_test_cases()
    results_mgr = ResultsManager()
    all_results = {}
    
    # Model configurations to test
    configs = [
        {
            "name": "Mock System",
            "connector": MockConnector(response="4. This is a mock response."),
            "enabled": True
        },
    ]
    
    # Add OpenAI models if API key is available
    if has_openai:
        configs.extend([
            {
                "name": "GPT-3.5",
                "connector": OpenAIConnector(model="gpt-3.5-turbo"),
                "enabled": True
            },
            {
                "name": "GPT-4",
                "connector": OpenAIConnector(model="gpt-4"),
                "enabled": True
            },
        ])
    else:
        print("⚠️  OPENAI_API_KEY not found - skipping OpenAI models")
        print("   Set OPENAI_API_KEY in .env to test with real models\n")
    
    # Run tests for each configuration
    for config in configs:
        if not config.get("enabled", True):
            continue
        
        print(f"\n{'='*60}")
        print(f"Testing: {config['name']}")
        print(f"{'='*60}")
        
        runner = TestRunner(config["connector"], verbose=False)
        results = runner.run_suite(test_cases, suite_name=config["name"])
        
        all_results[config["name"]] = results
        
        # Print summary
        print(f"\nPass Rate: {results.overall_pass_rate*100:.1f}%")
        print(f"Avg Score: {results.average_score:.2f}")
        print(f"Total Time: {results.total_time:.2f}s")
        
        # Save results
        results_mgr.save_results(results)
    
    # Print comparison
    print(f"\n{'='*60}")
    print("COMPARISON SUMMARY")
    print(f"{'='*60}")
    print(f"{'System':<20} {'Pass Rate':<12} {'Avg Score':<12} {'Time':<10}")
    print("-" * 60)
    
    for name, results in all_results.items():
        print(
            f"{name:<20} "
            f"{results.overall_pass_rate*100:>6.1f}%     "
            f"{results.average_score:>6.2f}       "
            f"{results.total_time:>6.2f}s"
        )
    
    # Find best performer
    if all_results:
        best = max(all_results.items(), key=lambda x: x[1].overall_pass_rate)
        print(f"\n🏆 Best performer: {best[0]}")


if __name__ == '__main__':
    main()

