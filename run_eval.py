#!/usr/bin/env python3
"""
Main CLI entry point for running evaluations
"""

import argparse
import yaml
import sys
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

from eval_framework import TestRunner, TestCase, ResultsManager, get_connector

# Load environment variables
load_dotenv()


def load_test_suite(yaml_path: str) -> Dict[str, Any]:
    """Load test suite from YAML file"""
    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(
        description="Run LLM/Application Evaluations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run a test suite
  python run_eval.py --test-suite test_cases/example.yaml
  
  # Use a specific connector
  python run_eval.py --test-suite test_cases/example.yaml --connector openai --model gpt-4
  
  # Don't save results
  python run_eval.py --test-suite test_cases/example.yaml --no-save
  
  # Quiet mode
  python run_eval.py --test-suite test_cases/example.yaml --quiet
        """
    )
    
    parser.add_argument(
        '--test-suite',
        type=str,
        required=True,
        help='Path to YAML test suite file'
    )
    
    parser.add_argument(
        '--connector',
        type=str,
        default='mock',
        choices=['openai', 'anthropic', 'custom_app', 'mock'],
        help='Connector type to use (default: mock)'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        help='Model to use (for LLM connectors)'
    )
    
    parser.add_argument(
        '--api-url',
        type=str,
        help='API URL (for custom_app connector)'
    )
    
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Don\'t save results to file'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Output filename for results'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Minimal output (no progress)'
    )
    
    parser.add_argument(
        '--detail',
        type=str,
        help='Show detailed results for a specific test'
    )
    
    args = parser.parse_args()
    
    # Load test suite
    try:
        suite_data = load_test_suite(args.test_suite)
    except FileNotFoundError:
        print(f"Error: Test suite file not found: {args.test_suite}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")
        sys.exit(1)
    
    # Parse test cases
    test_cases = [TestCase.from_dict(tc) for tc in suite_data.get('test_cases', [])]
    
    if not test_cases:
        print("Error: No test cases found in test suite")
        sys.exit(1)
    
    suite_name = suite_data.get('name', 'Test Suite')
    suite_description = suite_data.get('description', '')
    
    if not args.quiet:
        print(f"\nTest Suite: {suite_name}")
        if suite_description:
            print(f"Description: {suite_description}")
    
    # Create connector
    connector_kwargs = {}
    if args.model:
        connector_kwargs['model'] = args.model
    if args.api_url:
        connector_kwargs['api_url'] = args.api_url
    
    try:
        connector = get_connector(args.connector, **connector_kwargs)
    except Exception as e:
        print(f"Error creating connector: {e}")
        sys.exit(1)
    
    # Create test runner
    runner = TestRunner(connector, verbose=not args.quiet)
    
    # Run tests
    suite_result = runner.run_suite(
        test_cases,
        suite_name=suite_name
    )
    
    # Results manager
    results_mgr = ResultsManager()
    
    # Save results
    if not args.no_save:
        output_path = results_mgr.save_results(suite_result, filename=args.output)
        if not args.quiet:
            print(f"Results saved to: {output_path}")
    
    # Print summary
    if not args.quiet:
        results_mgr.print_summary(suite_result)
    
    # Print detailed results if requested
    if args.detail:
        results_mgr.print_test_detail(suite_result, args.detail)
    
    # Exit with appropriate code
    sys.exit(0 if suite_result.failed_tests == 0 else 1)


if __name__ == '__main__':
    main()

