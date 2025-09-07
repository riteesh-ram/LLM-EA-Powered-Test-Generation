#!/usr/bin/env python3
"""
Mutant Tester Module

This module handles testing individual mutants against test suites.
Single responsibility: Test mutants and return results.
"""

import subprocess
import time
import shutil as shutil_module
import os
import re
from pathlib import Path
from typing import Tuple, Optional
import logging


class MutantTester:
    """Handles testing individual mutants against test suites."""
    
    def __init__(self, module_name: str, logger: Optional[logging.Logger] = None):
        """
        Initialize mutant tester.
        """
        self.module_name = module_name
        self.logger = logger or logging.getLogger(__name__)
        
        # Define paths using absolute paths to prevent any relative path issues
        # When running from llm_testgen directory: python mutants_validation/pipeline_mutant_generator.py
        # Get the absolute path to the llm_testgen directory
        current_working_dir = Path.cwd().resolve()  # This is llm_testgen directory (absolute)
        self.source_dir = current_working_dir / "tests" / "source"
        self.test_dir = current_working_dir / "tests" / "test_suites"
        # Use temp_test_dir specifically within mutants_validation folder (absolute path)
        self.temp_dir = current_working_dir / "mutants_validation" / "temp_test_dir"
        
        # File paths
        self.source_file = self.source_dir / f"{module_name}.py"
        self.test_file = self.test_dir / f"llm_generated_test_{module_name}.py"
        
        # Python executable (use mutpy environment) - dynamic path resolution
        mutpy_env_dir = current_working_dir / "mutants_validation" / "mutpy_env"
        self.python_executable = str(mutpy_env_dir / "bin" / "python")
        
        # Validate that the mutpy environment exists
        if not Path(self.python_executable).exists():
            self.logger.warning(f"MutPy environment not found at: {self.python_executable}")
            self.logger.warning("Falling back to system Python")
            self.python_executable = "python"
        
        # Ensure temp directory exists
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def set_test_file(self, test_file_path: str):
        """Set a custom test file path for testing."""
        self.test_file = Path(test_file_path)
    
    def test_single_mutant(self, source_content: str, mutant_name: str) -> Tuple[str, int, int, int, str, str]:
        """
        Test a single mutant against the test suite.
        """
        try:
            # Clear cache directories
            cache_dirs = [self.temp_dir / "__pycache__", self.temp_dir / ".pytest_cache"]
            for cache_dir in cache_dirs:
                if cache_dir.exists():
                    shutil_module.rmtree(cache_dir)
            
            # Create temporary source file with mutant content
            temp_source_path = self.temp_dir / f"{self.module_name}.py"
            with open(temp_source_path, 'w') as f:
                f.write(source_content)
            
            # Copy test file to temp directory and modify import paths
            temp_test_path = self.temp_dir / f"test_{self.module_name}.py"
            with open(self.test_file, 'r') as f:
                test_content = f.read()
            
            # Fix the import path in the test file to work in temp directory
            # Replace the dynamic path resolution with direct import since both files are in same dir
            modified_test_content = test_content.replace(
                f'''# Add the tests/source directory to Python path to import the source module
current_dir = Path(__file__).parent
source_dir = current_dir.parent / "source"
sys.path.insert(0, str(source_dir))

import {self.module_name}''',
                f'''# Import the source module directly (both files are in same temp directory)
import {self.module_name}'''
            )
            
            # Also handle cases where the import might be formatted differently
            if modified_test_content == test_content:  # If the above replacement didn't work
                # Try alternative patterns
                import re
                # Pattern to match the path addition and import
                pattern = r'(# Add.*?import the source module.*?sys\.path\.insert\(0.*?\)\s*)(import\s+' + re.escape(self.module_name) + r')'
                modified_test_content = re.sub(pattern, r'# Import the source module directly (both files are in same temp directory)\n\2', test_content, flags=re.DOTALL)
            
            # Debug: Print if the replacement worked
            if self.logger:
                if modified_test_content != test_content:
                    self.logger.info(f"Successfully modified test file import paths for {mutant_name}")
                else:
                    self.logger.warning(f"Failed to modify test file import paths for {mutant_name}")
                    # Print first few lines of test content for debugging
                    self.logger.warning("Original test file first 10 lines:")
                    for i, line in enumerate(test_content.splitlines()[:10], 1):
                        self.logger.warning(f"  {i}: {line}")
            
            with open(temp_test_path, 'w') as f:
                f.write(modified_test_content)
            
            # Run the test with timeout in isolated environment
            start_time = time.time()
            
            # Set environment variables to prevent unwanted directory creation
            env = os.environ.copy()
            env['PYTHONDONTWRITEBYTECODE'] = '1'  # Prevent .pyc file creation
            env['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'  # Disable plugin autoload
            
            result = subprocess.run(
                [self.python_executable, "-m", "pytest", str(temp_test_path), "-v", "--tb=short"],
                capture_output=True,
                timeout=30,  # 30 second timeout
                text=True,
                cwd=str(self.temp_dir),  # Run in isolated temp directory
                env=env  # Use modified environment
            )
            execution_time = time.time() - start_time
            
            # Parse pytest output to get test counts
            stdout = result.stdout
            stderr = result.stderr
            num_tests = 0
            num_pass = 0
            num_fail = 0
            
            # Debug: Log pytest output for debugging
            if self.logger and (result.returncode != 0 or num_tests == 0):
                self.logger.debug(f"Pytest stdout for {mutant_name}:")
                for line in stdout.splitlines()[:20]:  # Limit lines for readability
                    self.logger.debug(f"  STDOUT: {line}")
                if stderr:
                    self.logger.debug(f"Pytest stderr for {mutant_name}:")
                    for line in stderr.splitlines()[:20]:
                        self.logger.debug(f"  STDERR: {line}")
            
            # Parse pytest summary line
            for line in stdout.split('\n'):
                if ' passed' in line and ('failed' in line or 'error' in line):
                    # Format: "X failed, Y passed in Zs"
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'failed,' and i > 0:
                            num_fail = int(parts[i-1])
                        elif part == 'passed' and i > 0:
                            num_pass = int(parts[i-1])
                elif ' passed in ' in line:
                    # Format: "X passed in Zs"
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'passed' and i > 0:
                            num_pass = int(parts[i-1])
                elif ' failed in ' in line:
                    # Format: "X failed in Zs"
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'failed' and i > 0:
                            num_fail = int(parts[i-1])
            
            num_tests = num_pass + num_fail
            
            # Determine overall status
            if result.returncode == 0:
                status = "PASS"
                self.logger.info(f"\\033[93m{mutant_name}\\033[92m -> All Tests Passed ({num_pass}/{num_tests}) - Mutant SURVIVED\\033[0m")
            else:
                status = "FAIL"
                if num_tests > 0:
                    self.logger.info(f"\\033[93m{mutant_name}\\033[91m -> Tests Failed ({num_pass}/{num_tests}) - Mutant KILLED\\033[0m")
                else:
                    self.logger.info(f"\\033[93m{mutant_name}\\033[91m -> Runtime Error (0 tests) - PROBLEMATIC\\033[0m")
            
            return status, num_tests, num_pass, num_fail, f"{execution_time:.2f}s", ""
            
        except subprocess.TimeoutExpired:
            self.logger.info(f"\\033[93m{mutant_name}\\033[94m -> Timeout (>30s)\\033[0m")
            return "TIMEOUT", 0, 0, 1, "30.0s", "Timeout"
        except Exception as e:
            self.logger.info(f"\\033[93m{mutant_name}\\033[91m -> Exception: {str(e)}\\033[0m")
            return "ERROR", 0, 0, 1, "0.0s", str(e)
        finally:
            # Clean up temporary files and any cache directories that might have been created
            temp_source_path = self.temp_dir / f"{self.module_name}.py"
            temp_test_path = self.temp_dir / f"test_{self.module_name}.py"
            
            if temp_source_path.exists():
                temp_source_path.unlink()
            if temp_test_path.exists():
                temp_test_path.unlink()
            
            # Also clean up any cache directories that might have been created
            cache_dirs_to_clean = [
                self.temp_dir / "__pycache__", 
                self.temp_dir / ".pytest_cache",
                # Prevent any cache directories from being created in parent directories
                self.temp_dir.parent / "__pycache__",
                self.temp_dir.parent.parent / "__pycache__"
            ]
            for cache_dir in cache_dirs_to_clean:
                if cache_dir.exists() and cache_dir.is_dir():
                    try:
                        shutil_module.rmtree(cache_dir)
                    except Exception:
                        pass  # Ignore cleanup errors
    
    def test_original_source(self) -> Tuple[str, int, int, int, str, str]:
        """
        Test the original source code to establish baseline.
        """
        with open(self.source_file, 'r') as f:
            original_content = f.read()
        
        return self.test_single_mutant(original_content, f"original_{self.module_name}")
