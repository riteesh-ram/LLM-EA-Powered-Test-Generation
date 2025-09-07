"""
Test Suite Manager for saving and running generated tests.
"""

import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from generation.config import TEST_SUITES_DIR, MAX_REPAIR_ATTEMPTS

class TestSuiteManager:
    #Manages saving and running generated test suites.
    
    def __init__(self):
        self.test_dir = Path(TEST_SUITES_DIR)
        self.test_dir.mkdir(parents=True, exist_ok=True)
    def save_test_suite(self, test_code: str, source_filename: str) -> str:
        #Save generated test code to a file.
        
        cleaned_code = self._clean_test_code(test_code)
        base_name = source_filename.replace('.py', '')
        test_filename = f"llm_generated_test_{base_name}.py"
        test_path = self.test_dir / test_filename
        try:
            with open(test_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_code)
            print(f"Test suite saved: {test_path}")
            return str(test_path)
        except Exception as e:
            print(f"Failed to save test suite: {e}")
            return None
    
    def _clean_test_code(self, test_code: str) -> str:
        """Clean and format the generated test code."""
        # Remove markdown code blocks if present
        if "```python" in test_code:
            # Extract code between ```python and ```
            match = re.search(r'```python\s*\n(.*?)\n```', test_code, re.DOTALL)
            if match:
                test_code = match.group(1)
        elif "```" in test_code:
            # Extract code between ``` and ```
            match = re.search(r'```\s*\n(.*?)\n```', test_code, re.DOTALL)
            if match:
                test_code = match.group(1)
        
        # Remove any leading/trailing whitespace
        test_code = test_code.strip()
        
        # Ensure proper formatting
        lines = test_code.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip empty lines at the beginning
            if not cleaned_lines and not line.strip():
                continue
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def run_tests(self, test_file_path: str, source_dir: str = None) -> dict:
        """
        Run pytest on the generated test file and print the full output as in manual runs.
        Returns the full output for LLM reprompting.
        """
        try:
            env = os.environ.copy()
            if source_dir:
                current_path = env.get('PYTHONPATH', '')
                env['PYTHONPATH'] = f"{source_dir}:{current_path}" if current_path else source_dir

            print(f"Running tests: {os.path.basename(test_file_path)}")
            print(f"Test file path: {test_file_path}")
            print(f"File exists: {os.path.exists(test_file_path)}")

            # Check if test file exists
            if not os.path.exists(test_file_path):
                error_msg = f"Test file not found: {test_file_path}"
                print(f"{error_msg}")
                return {
                    'success': False,
                    'return_code': -1,
                    'stdout': '',
                    'stderr': error_msg,
                    'output': error_msg
                }

            # Convert to absolute path and find project root
            absolute_test_path = Path(test_file_path).resolve()
            project_root = Path(__file__).parent.parent  # llm_testgen directory
            
            print(f"Project root: {project_root}")
            print(f"Absolute test path: {absolute_test_path}")
            
            cmd = [sys.executable, '-m', 'pytest', str(absolute_test_path), '-v', '--tb=long', '--no-header']
            print(f"Command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd=str(project_root)
            )

            # Print the full output exactly as pytest would
            full_output = (result.stdout or '') + (result.stderr or '')
            print("&"*40)
            print(f'output is: {full_output}')
            print("&"*40)

            success = result.returncode == 0
            if success:
                print("All tests passed!")
            else:
                print("Some tests failed")

            return {
                'success': success,
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'output': full_output
            }
        except Exception as e:
            error_msg = f"Failed to run tests: {e}"
            print(f"{error_msg}")
            return {
                'success': False,
                'return_code': -1,
                'stdout': '',
                'stderr': error_msg,
                'output': error_msg
            }
    def repair_test_with_llm(self, error_output: str, source_filename: str = None) -> str:
        #Send only pytest error output to LLM for repair - no source file upload.
        try:
            # Import here to avoid circular imports
            import sys
            from pathlib import Path
            current_dir = Path(__file__).parent
            generation_dir = current_dir.parent / "generation"
            sys.path.insert(0, str(generation_dir))
            from generation.simple_llm import send_prompt_to_llm
            
            # Extract module name from filename or error output
            module_name = "sample_calculator"  # default
            if source_filename:
                module_name = source_filename.replace('.py', '')
            elif "import " in error_output:
                # Try to extract module name from error output
                import re
                match = re.search(r'import (\w+)', error_output)
                if match:
                    module_name = match.group(1)
            
            repair_prompt = f"""
The pytest execution failed with the following error:

ERROR OUTPUT:
```
{error_output}
```

Please regenerate a complete test suite that fixes these issues. 

REQUIREMENTS:
1. Fix all import issues - ALWAYS start your test file with these exact lines:
   ```python
   import pytest
   import sys
   from pathlib import Path
   
   # Add the tests/source directory to Python path to import the source module
   current_dir = Path(__file__).parent
   source_dir = current_dir.parent / "source"
   sys.path.insert(0, str(source_dir))
   
   import {module_name}
   ```
2. Ensure the test can find and import the source module correctly
3. Fix any syntax errors or test logic issues
4. Return ONLY the corrected Python test code without markdown formatting
5. Make sure the test file is self-contained and can run from the tests/test_suites directory
6. If tests are failing due to incorrect assumptions about function behavior, adjust the tests to match actual behavior

Generate the complete corrected test code:
"""
            print("Attempting to repair test with LLM...")
            print(f"Sending only error output to LLM (module: {module_name}, no source file upload)")
            # Don't pass source_file_path to avoid uploading/including source file
            repaired_code = send_prompt_to_llm(repair_prompt)
            if repaired_code:
                print("Test repair completed")
                return repaired_code
            else:
                print("Test repair failed")
                return None
        except Exception as e:
            print(f"Test repair error: {e}")
            return None

    def save_and_run_tests_with_repair(self, test_code: str, source_filename: str, source_file_path: str, max_repair_attempts: int = None) -> dict:
        """
        Save test suite and run with automatic repair if it fails.
        The repaired test suite will overwrite the original test file.
        """
        if max_repair_attempts is None:
            max_repair_attempts = MAX_REPAIR_ATTEMPTS
            
        # Save initial test file
        test_file_path = self.save_test_suite(test_code, source_filename)
        if not test_file_path:
            return {'success': False, 'error': 'Failed to save test file'}
        
        source_dir = os.path.dirname(source_file_path)
        attempt = 0
        
        while attempt <= max_repair_attempts:
            if attempt > 0:
                print(f"\nRepair attempt {attempt}/{max_repair_attempts}")
                print(f"Overwriting test file: {test_file_path}")
            
            # Run tests on current test file
            results = self.run_tests(test_file_path, source_dir)
            
            if results['success']:
                print(f"Tests passed on attempt {attempt + 1}!")
                return results
            
            if attempt >= max_repair_attempts:
                print(f"Test repair failed after {max_repair_attempts} attempts")
                return results
            
            # Get repaired code from LLM (sending only error output, no source file)
            repaired_code = self.repair_test_with_llm(results['output'], source_filename)
            
            if repaired_code:
                # Overwrite the same test file with repaired code
                try:
                    cleaned_repaired_code = self._clean_test_code(repaired_code)
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
    
    def print_test_results(self, results: dict):
        #Print formatted test results.
        print("\n" + "="*60)
        print("TEST RESULTS")
        print("="*60)
        if results['success']:
            print("Status: SUCCESS")
        else:
            print("Status: FAILED")
        print(f"Return code: {results['return_code']}")
        if results['output']:
            print("\nCOMPLETE OUTPUT:")
            print("-" * 30)
            print(results['output'])
        if results['stdout'] and results['stdout'].strip():
            print("\nSTDOUT:")
            print("-" * 30)
            print(results['stdout'])
        if results['stderr'] and results['stderr'].strip():
            print("\nSTDERR:")
            print("-" * 30)
            print(results['stderr'])
        print("="*60)


# Global instance
_test_manager = None

def get_test_manager():
    #Get or create test suite manager instance.
    global _test_manager
    if _test_manager is None:
        _test_manager = TestSuiteManager()
    return _test_manager
