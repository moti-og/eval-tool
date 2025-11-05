"""
Test execution and orchestration
"""

import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field, asdict

from .connectors import BaseConnector, get_connector
from .evaluators import evaluate_result, EvalResult


@dataclass
class TestCase:
    """Single test case"""
    name: str
    input: Any
    evaluators: List[Dict[str, Any]]
    expected_output: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TestCase':
        return cls(
            name=data.get("name", "Unnamed test"),
            input=data.get("input"),
            evaluators=data.get("evaluators", []),
            expected_output=data.get("expected_output"),
            metadata=data.get("metadata", {})
        )


@dataclass
class TestResult:
    """Result of running a single test case"""
    test_name: str
    input: Any
    output: str
    expected_output: Optional[str]
    eval_results: List[EvalResult]
    passed: bool
    overall_score: float
    execution_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "test_name": self.test_name,
            "input": str(self.input),
            "output": self.output,
            "expected_output": self.expected_output,
            "eval_results": [
                {
                    "passed": r.passed,
                    "score": r.score,
                    "evaluator_type": r.evaluator_type,
                    "details": r.details,
                    "error": r.error
                }
                for r in self.eval_results
            ],
            "passed": self.passed,
            "overall_score": self.overall_score,
            "execution_time": self.execution_time,
            "metadata": self.metadata,
            "error": self.error
        }


@dataclass
class TestSuiteResult:
    """Result of running a full test suite"""
    suite_name: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    overall_pass_rate: float
    average_score: float
    total_time: float
    test_results: List[TestResult]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "suite_name": self.suite_name,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "overall_pass_rate": self.overall_pass_rate,
            "average_score": self.average_score,
            "total_time": self.total_time,
            "test_results": [r.to_dict() for r in self.test_results],
            "metadata": self.metadata
        }


class TestRunner:
    """Orchestrates test execution"""
    
    def __init__(
        self,
        connector: BaseConnector,
        custom_evaluators: Optional[Dict[str, Callable]] = None,
        verbose: bool = True
    ):
        """
        Initialize test runner
        
        Args:
            connector: Connector to use for calling the system under test
            custom_evaluators: Dict of custom evaluator functions
            verbose: Print progress during execution
        """
        self.connector = connector
        self.custom_evaluators = custom_evaluators or {}
        self.verbose = verbose
    
    def run_test(self, test_case: TestCase, **connector_kwargs) -> TestResult:
        """
        Run a single test case
        
        Args:
            test_case: TestCase to run
            **connector_kwargs: Additional arguments to pass to connector
            
        Returns:
            TestResult with evaluation results
        """
        start_time = time.time()
        
        try:
            # Call the system
            output = self.connector.call(test_case.input, **connector_kwargs)
            
            # Evaluate the output
            eval_results = evaluate_result(
                output=output,
                evaluators=test_case.evaluators,
                expected=test_case.expected_output,
                custom_evaluators=self.custom_evaluators
            )
            
            # Determine if test passed (all evaluators must pass)
            passed = all(r.passed for r in eval_results)
            
            # Calculate overall score (average of all evaluator scores)
            overall_score = sum(r.score for r in eval_results) / len(eval_results) if eval_results else 0.0
            
            execution_time = time.time() - start_time
            
            return TestResult(
                test_name=test_case.name,
                input=test_case.input,
                output=output,
                expected_output=test_case.expected_output,
                eval_results=eval_results,
                passed=passed,
                overall_score=overall_score,
                execution_time=execution_time,
                metadata=test_case.metadata
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            return TestResult(
                test_name=test_case.name,
                input=test_case.input,
                output="",
                expected_output=test_case.expected_output,
                eval_results=[],
                passed=False,
                overall_score=0.0,
                execution_time=execution_time,
                metadata=test_case.metadata,
                error=str(e)
            )
    
    def run_suite(
        self,
        test_cases: List[TestCase],
        suite_name: str = "Test Suite",
        **connector_kwargs
    ) -> TestSuiteResult:
        """
        Run a full test suite
        
        Args:
            test_cases: List of test cases to run
            suite_name: Name of the test suite
            **connector_kwargs: Additional arguments to pass to connector
            
        Returns:
            TestSuiteResult with all test results
        """
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Running test suite: {suite_name}")
            print(f"Total tests: {len(test_cases)}")
            print(f"{'='*60}\n")
        
        start_time = time.time()
        test_results = []
        
        for i, test_case in enumerate(test_cases, 1):
            if self.verbose:
                print(f"[{i}/{len(test_cases)}] Running: {test_case.name}...")
            
            result = self.run_test(test_case, **connector_kwargs)
            test_results.append(result)
            
            if self.verbose:
                status = "✓ PASSED" if result.passed else "✗ FAILED"
                print(f"  {status} (score: {result.overall_score:.2f}, time: {result.execution_time:.2f}s)")
                if result.error:
                    print(f"  Error: {result.error}")
                print()
        
        total_time = time.time() - start_time
        
        # Calculate summary statistics
        passed_tests = sum(1 for r in test_results if r.passed)
        failed_tests = len(test_results) - passed_tests
        overall_pass_rate = passed_tests / len(test_results) if test_results else 0.0
        average_score = sum(r.overall_score for r in test_results) / len(test_results) if test_results else 0.0
        
        suite_result = TestSuiteResult(
            suite_name=suite_name,
            total_tests=len(test_cases),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            overall_pass_rate=overall_pass_rate,
            average_score=average_score,
            total_time=total_time,
            test_results=test_results
        )
        
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Test Suite Complete: {suite_name}")
            print(f"{'='*60}")
            print(f"Total: {suite_result.total_tests}")
            print(f"Passed: {suite_result.passed_tests} ({suite_result.overall_pass_rate*100:.1f}%)")
            print(f"Failed: {suite_result.failed_tests}")
            print(f"Average Score: {suite_result.average_score:.2f}")
            print(f"Total Time: {suite_result.total_time:.2f}s")
            print(f"{'='*60}\n")
        
        return suite_result

