#!/usr/bin/env python3
"""
Simple Statement Coverage Analysis Script

This script provides statement coverage analysis for test files.

Usage:
    python coverage_analysis/run_coverage_analysis.py <test_file_name>

Features:
- Statement coverage only
- Simple terminal output
- Automatic source file detection
"""

import sys
import os
import subprocess
import re
from pathlib import Path


class CoverageAnalyzer:
    """Simple coverage analyzer for statement coverage only."""
    
    def __init__(self, project_root: Path = None):
        """Initialize the coverage analyzer."""
        self.project_root = project_root or Path(__file__).parent.parent
        self.tests_dir = self.project_root / "tests"
        self.test_suites_dir = self.tests_dir / "test_suites"
        self.source_dir = self.tests_dir / "source"
        
        print(f"Coverage Analyzer initialized:")
        print(f"  - Project root: {self.project_root}")
        print(f"  - Test suites: {self.test_suites_dir}")
        print(f"  - Source directory: {self.source_dir}")
    
    def find_test_file(self, test_file_name: str) -> Path:
        """Find the full path to the test file."""
        # Handle full path input
        if "/" in test_file_name or "\\" in test_file_name:
            test_path = Path(test_file_name)
            if not test_path.is_absolute():
                test_path = self.project_root / test_path
            
            if not test_path.suffix:
                test_path = test_path.with_suffix('.py')
            
            if test_path.exists():
                return test_path
            else:
                test_file_name = test_path.stem
        
        # Remove .py extension if present
        if test_file_name.endswith('.py'):
            test_file_name = test_file_name[:-3]
        
        # Look in test_suites directory
        test_file = self.test_suites_dir / f"{test_file_name}.py"
        if test_file.exists():
            return test_file
        
        # Look in subdirectories
        for test_file in self.test_suites_dir.rglob(f"{test_file_name}.py"):
            return test_file
        
        raise FileNotFoundError(f"Test file not found: {test_file_name}.py")
    
    def detect_source_module(self, test_file: Path) -> tuple[str, Path]:
        """Detect which source module the test file is testing."""
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for import statements
            import_match = re.search(r'^import\s+(\w+)$', content, re.MULTILINE)
            if import_match:
                module_name = import_match.group(1)
                source_file = self.source_dir / f"{module_name}.py"
                if source_file.exists():
                    return module_name, source_file
            
            from_import_match = re.search(r'^from\s+(\w+)\s+import', content, re.MULTILINE)
            if from_import_match:
                module_name = from_import_match.group(1)
                source_file = self.source_dir / f"{module_name}.py"
                if source_file.exists():
                    return module_name, source_file
            
            # Extract from test file name
            test_name = test_file.stem
            for prefix in ['llm_generated_test_', 'pynguin_generated_test_', 'test_']:
                if test_name.startswith(prefix):
                    module_name = test_name[len(prefix):]
                    source_file = self.source_dir / f"{module_name}.py"
                    if source_file.exists():
                        return module_name, source_file
            
            raise ValueError(f"Could not detect source module for test file: {test_file}")
            
        except Exception as e:
            raise ValueError(f"Error detecting source module: {e}")
    
    def run_coverage_analysis(self, test_file_name: str) -> dict:
        """Run statement coverage analysis for a specific test file."""
        print("=" * 60)
        print("STATEMENT COVERAGE ANALYSIS")
        print("=" * 60)
        
        try:
            # Find test file
            test_file = self.find_test_file(test_file_name)
            print(f"Test file found: {test_file}")
            
            # Detect source module
            source_module, source_file = self.detect_source_module(test_file)
            print(f"Source module detected: {source_module}")
            
            print("\n" + "=" * 40)
            print("RUNNING COVERAGE ANALYSIS")
            print("=" * 40)
            
            # Set up environment
            env = os.environ.copy()
            source_path = str(self.source_dir)
            current_pythonpath = env.get('PYTHONPATH', '')
            if current_pythonpath:
                env['PYTHONPATH'] = f"{source_path}:{current_pythonpath}"
            else:
                env['PYTHONPATH'] = source_path
            
            # Build simple pytest command with coverage
            cmd = [
                sys.executable, '-m', 'pytest',
                str(test_file),
                f'--cov={source_module}',
                '--cov-report=term',
                '-v'
            ]
            
            print(f"Command: {' '.join(cmd)}")
            print(f"Analyzing module: {source_module}")
            
            # Run coverage analysis
            result = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                env=env,
                capture_output=True,
                text=True
            )
            
            print("\n" + "=" * 40)
            print("COVERAGE RESULTS")
            print("=" * 40)
            
            # Print pytest output
            if result.stdout:
                print(result.stdout)
            
            if result.stderr:
                print("STDERR:")
                print(result.stderr)
            
            # Parse coverage report
            coverage_percentage = self._parse_coverage_report(result.stdout)
            
            # Print summary
            print("\n" + "=" * 40)
            print("COVERAGE SUMMARY")
            print("=" * 40)
            print(f"Test file: {test_file.name}")
            print(f"Source module: {source_module}.py")
            print(f"Statement Coverage: {coverage_percentage}")
            print("=" * 40)
            
            return {
                'success': result.returncode == 0,
                'test_file': str(test_file),
                'source_module': source_module,
                'coverage_percentage': coverage_percentage,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
        except Exception as e:
            print(f"Coverage analysis failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _parse_coverage_report(self, report_output: str) -> str:
        """Parse coverage report to extract statement coverage percentage."""
        # Look for the TOTAL line with coverage percentage
        for line in report_output.splitlines():
            if 'TOTAL' in line and '%' in line:
                # Extract percentage using regex
                match = re.search(r'(\d+%)', line)
                if match:
                    return match.group(1)
        return 'N/A'


def main():
    """Main function for statement coverage analysis."""
    if len(sys.argv) != 2:
        print("Usage: python coverage_analysis/run_coverage_analysis.py <test_file_name>")
        print("")
        print("Examples:")
        print("  python coverage_analysis/run_coverage_analysis.py llm_generated_test_sample_utility")
        print("  python coverage_analysis/run_coverage_analysis.py tests/test_suites/llm_generated_test_sample_number")
        print("")
        print("Coverage Type:")
        print(" Statement Coverage - Which lines were executed")
        sys.exit(1)
    
    test_file_name = sys.argv[1]
    
    # Initialize analyzer
    analyzer = CoverageAnalyzer()
    
    # Run coverage analysis
    results = analyzer.run_coverage_analysis(test_file_name)
    
    if results['success']:
        print("\nStatement coverage analysis completed successfully!")
        print(f"Coverage: {results['coverage_percentage']}")
        sys.exit(0)
    else:
        print(f"\nCoverage analysis failed: {results.get('error', 'Unknown error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
