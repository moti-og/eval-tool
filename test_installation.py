#!/usr/bin/env python3
"""
Quick test to verify installation is working correctly
"""

import sys


def test_imports():
    """Test that all required packages can be imported"""
    print("Testing imports...")
    
    required_packages = [
        ('yaml', 'pyyaml'),
        ('dotenv', 'python-dotenv'),
        ('rich', 'rich'),
    ]
    
    optional_packages = [
        ('openai', 'openai'),
        ('anthropic', 'anthropic'),
        ('sentence_transformers', 'sentence-transformers'),
        ('sklearn', 'scikit-learn'),
    ]
    
    failed = []
    
    # Test required packages
    for module, package in required_packages:
        try:
            __import__(module)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} - REQUIRED")
            failed.append(package)
    
    # Test optional packages
    for module, package in optional_packages:
        try:
            __import__(module)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ⚠ {package} - optional (install for full functionality)")
    
    return len(failed) == 0


def test_framework():
    """Test that the eval framework can be imported and used"""
    print("\nTesting eval framework...")
    
    try:
        from eval_framework import (
            TestRunner,
            TestCase,
            MockConnector,
            ResultsManager,
            evaluate_result
        )
        print("  ✓ Framework imports successful")
        
        # Test creating a simple test case
        connector = MockConnector(response="Test response")
        test_case = TestCase(
            name="Installation test",
            input="test",
            evaluators=[{"type": "contains", "value": "Test"}]
        )
        
        runner = TestRunner(connector, verbose=False)
        result = runner.run_test(test_case)
        
        if result.passed:
            print("  ✓ Test execution successful")
            return True
        else:
            print("  ✗ Test execution failed")
            return False
            
    except Exception as e:
        print(f"  ✗ Framework test failed: {e}")
        return False


def test_yaml_loading():
    """Test that YAML test cases can be loaded"""
    print("\nTesting YAML test case loading...")
    
    try:
        import yaml
        from pathlib import Path
        
        test_file = Path("test_cases/example.yaml")
        if not test_file.exists():
            print("  ⚠ Example test case file not found")
            return True  # Not a critical error
        
        with open(test_file) as f:
            data = yaml.safe_load(f)
        
        if 'test_cases' in data and len(data['test_cases']) > 0:
            print(f"  ✓ Loaded {len(data['test_cases'])} test cases from example.yaml")
            return True
        else:
            print("  ✗ Invalid test case format")
            return False
            
    except Exception as e:
        print(f"  ✗ YAML loading failed: {e}")
        return False


def test_results_dir():
    """Test that results directory exists and is writable"""
    print("\nTesting results directory...")
    
    try:
        from pathlib import Path
        
        results_dir = Path("results")
        if not results_dir.exists():
            results_dir.mkdir()
            print("  ✓ Created results directory")
        else:
            print("  ✓ Results directory exists")
        
        # Test write permissions
        test_file = results_dir / ".test_write"
        test_file.write_text("test")
        test_file.unlink()
        print("  ✓ Results directory is writable")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Results directory test failed: {e}")
        return False


def main():
    print("="*60)
    print("Eval Tool Installation Test")
    print("="*60)
    
    tests = [
        ("Package imports", test_imports),
        ("Framework functionality", test_framework),
        ("YAML loading", test_yaml_loading),
        ("Results directory", test_results_dir),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        if test_func():
            passed += 1
        else:
            failed += 1
    
    print("\n" + "="*60)
    if failed == 0:
        print("✓ All tests passed! Installation is working correctly.")
        print("="*60)
        print("\nNext steps:")
        print("  1. Run: python run_eval.py --test-suite test_cases/example.yaml")
        print("  2. Check out QUICKSTART.md for more examples")
        print("  3. Create your own test cases in test_cases/")
        return 0
    else:
        print(f"✗ {failed} test(s) failed. Please fix the issues above.")
        print("="*60)
        print("\nTroubleshooting:")
        print("  - Run: pip install -r requirements.txt")
        print("  - Check that all required packages are installed")
        print("  - Make sure you're in the correct directory")
        return 1


if __name__ == '__main__':
    sys.exit(main())

