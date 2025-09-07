#!/usr/bin/env python3
"""
Simple runner for test suite merging with automatic repair functionality.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from test_merger import TestSuiteMerger
from initial_test_suite_generation.repair.test_suite_manager import TestSuiteManager
from initial_test_suite_generation.generation.config import MAX_REPAIR_ATTEMPTS


def main():
    """Main function with dynamic source file detection and repair functionality."""
    # Try to get module name from command line arguments or environment
    if len(sys.argv) > 1:
        source_file_name = sys.argv[1]
    else:
        # Default fallback, but we should detect the current module being processed
        source_file_name = os.environ.get('CURRENT_MODULE', 'sample_calculator')
    
    # Change working directory to project root
    original_cwd = os.getcwd()
    os.chdir(project_root)
    
    print("=" * 60)
    print("LLM + EA Test Suite Merger with Auto-Repair")
    print("=" * 60)
    print(f"Source file: {source_file_name}")
    print(f"Working from: {project_root}")
    print()
    
    try:
        merger = TestSuiteMerger(source_file_name)
        
        if merger.merge_test_suites():
            print("\n" + "=" * 60)
            print("Test suite merge completed successfully!")
            print("=" * 60)
            
            # Get the merged test file path
            merged_test_path = merger.get_merged_test_path()
            if not merged_test_path or not os.path.exists(merged_test_path):
                print("Cannot find merged test file for repair")
                return
                
            print(f"Merged test file: {merged_test_path}")
            
            # Run tests with automatic repair
            print("\nRunning merged tests with auto-repair functionality...")
            test_manager = TestSuiteManager()
            
            # Override the test directory to use project root
            test_manager.test_dir = project_root / "tests" / "test_suites"
            test_manager.test_dir.mkdir(parents=True, exist_ok=True)
            
            # Run the test file with repair mechanism
            repair_results = run_tests_with_repair(
                test_manager, 
                merged_test_path, 
                source_file_name
            )
            
            if repair_results['success']:
                print("\nAll tests are working correctly!")
                test_manager.print_test_results(repair_results)
            else:
                print(f"\nTests failed after {MAX_REPAIR_ATTEMPTS} repair attempts")
                test_manager.print_test_results(repair_results)
                
        else:
            print("\nTest suite merge failed!")
            
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Restore original working directory
        os.chdir(original_cwd)


def run_tests_with_repair(test_manager, test_file_path, source_filename):
    """
    Run tests with automatic repair mechanism.
    """
    # Use absolute paths relative to project root
    source_file_path = str(project_root / "tests" / "source" / f"{source_filename}.py")
    source_dir = str(project_root / "tests" / "source")
    attempt = 0
    
    print(f"Auto-repair enabled with max {MAX_REPAIR_ATTEMPTS} attempts")
    
    while attempt <= MAX_REPAIR_ATTEMPTS:
        if attempt > 0:
            print(f"\nRepair attempt {attempt}/{MAX_REPAIR_ATTEMPTS}")
            print(f"Testing repaired file: {os.path.basename(test_file_path)}")
        
        # Run tests on current test file
        results = test_manager.run_tests(test_file_path, source_dir)
        
        if results['success']:
            print(f"Tests passed on attempt {attempt + 1}!")
            return results
        
        if attempt >= MAX_REPAIR_ATTEMPTS:
            print(f"Test repair failed after {MAX_REPAIR_ATTEMPTS} attempts")
            return results
        
        print(f"Tests failed on attempt {attempt + 1}, attempting repair...")
        
        # Get repaired code from LLM (sending only error output, no source file)
        repaired_code = test_manager.repair_test_with_llm(results['output'], source_filename)
        
        if repaired_code:
            # Overwrite the test file with repaired code
            try:
                cleaned_repaired_code = test_manager._clean_test_code(repaired_code)
                with open(test_file_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned_repaired_code)
                print(f"Test file overwritten with repaired code: {test_file_path}")
                attempt += 1
            except Exception as e:
                print(f"Failed to overwrite test file: {e}")
                return results
        else:
            print("Could not repair test, stopping")
            return results
            
    return results


if __name__ == "__main__":
    main()
