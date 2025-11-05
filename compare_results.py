#!/usr/bin/env python3
"""
Utility script to compare two test results
"""

import argparse
import sys
from eval_framework import ResultsManager


def main():
    parser = argparse.ArgumentParser(
        description="Compare two test run results"
    )
    
    parser.add_argument(
        'result1',
        type=str,
        help='First result file (in results/ directory)'
    )
    
    parser.add_argument(
        'result2',
        type=str,
        help='Second result file (in results/ directory)'
    )
    
    args = parser.parse_args()
    
    results_mgr = ResultsManager()
    
    try:
        results_mgr.compare_results(args.result1, args.result2)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error comparing results: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

