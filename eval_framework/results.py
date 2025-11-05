"""
Results storage and reporting
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .runners import TestSuiteResult


class ResultsManager:
    """Manage test results - storage and reporting"""
    
    def __init__(self, results_dir: str = "results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        self.console = Console()
    
    def save_results(self, suite_result: TestSuiteResult, filename: Optional[str] = None) -> Path:
        """
        Save test results to JSON file
        
        Args:
            suite_result: TestSuiteResult to save
            filename: Optional filename (defaults to timestamp)
            
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = "".join(c if c.isalnum() else "_" for c in suite_result.suite_name)
            filename = f"{safe_name}_{timestamp}.json"
        
        filepath = self.results_dir / filename
        
        result_dict = suite_result.to_dict()
        result_dict["timestamp"] = datetime.now().isoformat()
        
        with open(filepath, 'w') as f:
            json.dump(result_dict, f, indent=2)
        
        return filepath
    
    def load_results(self, filename: str) -> dict:
        """Load results from JSON file"""
        filepath = self.results_dir / filename
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def print_summary(self, suite_result: TestSuiteResult):
        """Print a nice summary of test results"""
        
        # Summary panel
        pass_rate_color = "green" if suite_result.overall_pass_rate >= 0.8 else "yellow" if suite_result.overall_pass_rate >= 0.5 else "red"
        
        summary = Text()
        summary.append(f"Suite: {suite_result.suite_name}\n", style="bold")
        summary.append(f"Tests: {suite_result.total_tests} | ", style="white")
        summary.append(f"Passed: {suite_result.passed_tests} | ", style="green")
        summary.append(f"Failed: {suite_result.failed_tests}\n", style="red")
        summary.append(f"Pass Rate: ", style="white")
        summary.append(f"{suite_result.overall_pass_rate*100:.1f}%\n", style=pass_rate_color)
        summary.append(f"Avg Score: {suite_result.average_score:.2f}\n", style="cyan")
        summary.append(f"Time: {suite_result.total_time:.2f}s", style="white")
        
        self.console.print(Panel(summary, title="Test Results", border_style="blue"))
        
        # Detailed results table
        table = Table(title="Test Details")
        table.add_column("Test", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Score", justify="right")
        table.add_column("Time", justify="right")
        table.add_column("Details")
        
        for result in suite_result.test_results:
            status = "✓ PASS" if result.passed else "✗ FAIL"
            status_style = "green" if result.passed else "red"
            
            # Get evaluator details
            eval_details = []
            for eval_result in result.eval_results:
                if eval_result.passed:
                    eval_details.append(f"✓ {eval_result.evaluator_type}")
                else:
                    eval_details.append(f"✗ {eval_result.evaluator_type}")
            
            details_str = "\n".join(eval_details) if eval_details else (result.error or "")
            
            table.add_row(
                result.test_name,
                Text(status, style=status_style),
                f"{result.overall_score:.2f}",
                f"{result.execution_time:.2f}s",
                details_str
            )
        
        self.console.print(table)
    
    def print_test_detail(self, suite_result: TestSuiteResult, test_name: str):
        """Print detailed information about a specific test"""
        
        test_result = next((r for r in suite_result.test_results if r.test_name == test_name), None)
        
        if not test_result:
            self.console.print(f"[red]Test '{test_name}' not found[/red]")
            return
        
        # Test info
        self.console.print(f"\n[bold cyan]Test: {test_result.test_name}[/bold cyan]")
        self.console.print(f"Status: {'[green]PASSED[/green]' if test_result.passed else '[red]FAILED[/red]'}")
        self.console.print(f"Score: {test_result.overall_score:.2f}")
        self.console.print(f"Time: {test_result.execution_time:.2f}s\n")
        
        # Input/Output
        self.console.print(Panel(str(test_result.input), title="Input", border_style="blue"))
        
        if test_result.expected_output:
            self.console.print(Panel(test_result.expected_output, title="Expected Output", border_style="yellow"))
        
        self.console.print(Panel(test_result.output, title="Actual Output", border_style="green" if test_result.passed else "red"))
        
        # Evaluator results
        if test_result.eval_results:
            self.console.print("\n[bold]Evaluator Results:[/bold]")
            for eval_result in test_result.eval_results:
                status = "✓" if eval_result.passed else "✗"
                color = "green" if eval_result.passed else "red"
                self.console.print(f"  [{color}]{status} {eval_result.evaluator_type}[/{color}] (score: {eval_result.score:.2f})")
                
                if eval_result.details:
                    for key, value in eval_result.details.items():
                        self.console.print(f"    {key}: {value}")
                
                if eval_result.error:
                    self.console.print(f"    [red]Error: {eval_result.error}[/red]")
        
        if test_result.error:
            self.console.print(f"\n[red]Execution Error: {test_result.error}[/red]")
    
    def compare_results(self, filename1: str, filename2: str):
        """Compare two test runs"""
        results1 = self.load_results(filename1)
        results2 = self.load_results(filename2)
        
        self.console.print(f"\n[bold]Comparing Results:[/bold]")
        self.console.print(f"Run 1: {filename1}")
        self.console.print(f"Run 2: {filename2}\n")
        
        # Summary comparison
        table = Table(title="Comparison")
        table.add_column("Metric")
        table.add_column("Run 1", justify="right")
        table.add_column("Run 2", justify="right")
        table.add_column("Diff", justify="right")
        
        metrics = [
            ("Pass Rate", "overall_pass_rate", "%"),
            ("Avg Score", "average_score", ""),
            ("Total Time", "total_time", "s"),
        ]
        
        for metric_name, key, unit in metrics:
            val1 = results1[key]
            val2 = results2[key]
            diff = val2 - val1
            
            if unit == "%":
                val1_str = f"{val1*100:.1f}%"
                val2_str = f"{val2*100:.1f}%"
                diff_str = f"{diff*100:+.1f}%"
            else:
                val1_str = f"{val1:.2f}{unit}"
                val2_str = f"{val2:.2f}{unit}"
                diff_str = f"{diff:+.2f}{unit}"
            
            diff_color = "green" if diff > 0 else "red" if diff < 0 else "white"
            
            table.add_row(
                metric_name,
                val1_str,
                val2_str,
                Text(diff_str, style=diff_color)
            )
        
        self.console.print(table)

