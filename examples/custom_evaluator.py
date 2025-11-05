"""
Example: Using custom evaluators
"""

from eval_framework import TestRunner, TestCase, MockConnector


def custom_sentiment_check(output: str, expected: str = None, **kwargs) -> dict:
    """
    Custom evaluator: Check if output has positive sentiment
    """
    positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful']
    
    score = sum(1 for word in positive_words if word.lower() in output.lower())
    score = min(score / 2, 1.0)  # Normalize to 0-1
    
    return {
        "passed": score > 0.3,
        "score": score,
        "details": {
            "positive_words_found": score * 2,
            "threshold": 0.3
        }
    }


def custom_length_ratio(output: str, expected: str = None, **kwargs) -> bool:
    """
    Custom evaluator: Check if output is within 20% of expected length
    """
    if not expected:
        return True
    
    ratio = len(output) / len(expected)
    return 0.8 <= ratio <= 1.2


def main():
    # Create connector
    connector = MockConnector(response="This is a great and wonderful response")
    
    # Define custom evaluators
    custom_evaluators = {
        "sentiment_check": custom_sentiment_check,
        "length_ratio": custom_length_ratio,
    }
    
    # Define test cases using custom evaluators
    test_cases = [
        TestCase(
            name="Sentiment test",
            input="How do you feel?",
            evaluators=[
                {"type": "custom", "function": "sentiment_check"}
            ]
        ),
        TestCase(
            name="Length ratio test",
            input="Write something",
            expected_output="This should be about the same length as output",
            evaluators=[
                {"type": "custom", "function": "length_ratio"}
            ]
        ),
    ]
    
    # Create runner with custom evaluators
    runner = TestRunner(
        connector,
        custom_evaluators=custom_evaluators,
        verbose=True
    )
    
    # Run tests
    results = runner.run_suite(test_cases, suite_name="Custom Evaluator Suite")
    
    print(f"\nOverall pass rate: {results.overall_pass_rate*100:.1f}%")


if __name__ == '__main__':
    main()

