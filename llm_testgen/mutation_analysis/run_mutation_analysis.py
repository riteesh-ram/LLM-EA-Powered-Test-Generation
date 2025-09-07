#!/usr/bin/env python3
"""
Standalone Mutation Score Analysis Script

This script provides comprehensive mutation score analysis for individual test files using
the existing mutants_validation components. It reuses existing implementations for 
mutant generation, testing, and score calculation.

Usage:
    python mutation_analysis/run_mutation_analysis.py <test_file_name>

Features:
- Uses existing MutantGenerator, MutantTester, and MutationScoreCalculator
- Stores mutants in mutants_validation/generated_mutants
- Stores results in test_results with 'analysis_' prefix
- Independent operation from main pipeline
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add the mutants_validation directory to Python path to import existing modules
current_dir = Path(__file__).parent
mutants_validation_dir = current_dir.parent / "mutants_validation"
sys.path.insert(0, str(mutants_validation_dir))

# Import existing components from mutants_validation
from mutant_generator import MutantGenerator
from mutant_tester import MutantTester
from mutation_score_calculator import MutationScoreCalculator


class StandaloneMutationAnalyzer:
    """Standalone mutation analyzer using existing mutants_validation components."""
    
    def __init__(self, project_root: Path = None):
        """Initialize the standalone mutation analyzer."""
        self.project_root = project_root or Path(__file__).parent.parent
        self.tests_dir = self.project_root / "tests"
        self.test_suites_dir = self.tests_dir / "test_suites"
        self.source_dir = self.tests_dir / "source"
        
        # Use existing directories from mutants_validation
        self.mutants_validation_dir = self.project_root / "mutants_validation"
        self.generated_mutants_dir = self.mutants_validation_dir / "generated_mutants"
        
        # Use test_results directory for analysis results
        self.test_results_dir = self.project_root / "test_results"
        self.test_results_dir.mkdir(exist_ok=True)
        
        print(f"Standalone Mutation Analyzer initialized:")
        print(f"  - Project root: {self.project_root}")
        print(f"  - Tests directory: {self.tests_dir}")
        print(f"  - Test suites: {self.test_suites_dir}")
        print(f"  - Source directory: {self.source_dir}")
        print(f"  - Generated mutants: {self.generated_mutants_dir}")
        print(f"  - Analysis results: {self.test_results_dir}")
    
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
        
        # Look in pynguin_tests subdirectory
        pynguin_test_file = self.test_suites_dir / "pynguin_tests" / f"{test_file_name}.py"
        if pynguin_test_file.exists():
            return pynguin_test_file
        
        # Look for exact filename match
        for test_file in self.test_suites_dir.rglob(f"{test_file_name}.py"):
            return test_file
        
        raise FileNotFoundError(f"Test file not found: {test_file_name}.py")
    
    def detect_source_module(self, test_file: Path) -> tuple[str, Path]:
        """Detect which source module the test file is testing."""
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for import statements that reference source modules
            import re
            
            # Pattern 1: import module_name
            import_match = re.search(r'^import\s+(\w+)$', content, re.MULTILINE)
            if import_match:
                module_name = import_match.group(1)
                source_file = self.source_dir / f"{module_name}.py"
                if source_file.exists():
                    return module_name, source_file
            
            # Pattern 2: from module_name import ...
            from_import_match = re.search(r'^from\s+(\w+)\s+import', content, re.MULTILINE)
            if from_import_match:
                module_name = from_import_match.group(1)
                source_file = self.source_dir / f"{module_name}.py"
                if source_file.exists():
                    return module_name, source_file
            
            # Pattern 3: Extract from test file name
            test_name = test_file.stem
            for prefix in ['llm_generated_test_', 'pynguin_generated_test_', 'test_', 'mutants_killer_tests_']:
                if test_name.startswith(prefix):
                    module_name = test_name[len(prefix):]
                    source_file = self.source_dir / f"{module_name}.py"
                    if source_file.exists():
                        return module_name, source_file
            
            raise ValueError(f"Could not detect source module for test file: {test_file}")
            
        except Exception as e:
            raise ValueError(f"Error detecting source module: {e}")
    
    def run_mutation_analysis(self, test_file_name: str) -> dict:
        """Run comprehensive mutation score analysis using existing components."""
        print("=" * 80)
        print("STANDALONE MUTATION SCORE ANALYSIS")
        print("=" * 80)
        
        try:
            # Find test file
            test_file = self.find_test_file(test_file_name)
            print(f"Test file found: {test_file}")
            
            # Detect source module
            source_module, source_file = self.detect_source_module(test_file)
            print(f"Source module detected: {source_module} ({source_file})")
            
            # The existing components expect to run from llm_testgen directory
            # No need to change working directory as we're already in the right place
            
            # Initialize existing components with logger=None to use default logging
            print(f"\n" + "=" * 50)
            print("INITIALIZING EXISTING COMPONENTS")
            print("=" * 50)
            
            generator = MutantGenerator(source_module, logger=None)
            tester = MutantTester(source_module, logger=None)
            calculator = MutationScoreCalculator(source_module, logger=None)
            
            # Modify calculator to use analysis prefix and test_results directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            calculator.results_csv_path = self.test_results_dir / f"analysis_mutation_test_results_{source_module}_{timestamp}.csv"
            calculator.summary_path = self.test_results_dir / f"analysis_mutation_summary_{source_module}_{timestamp}.txt"
            
            print(f"MutantGenerator initialized for {source_module}")
            print(f"MutantTester initialized for {source_module}")
            print(f"MutationScoreCalculator initialized for {source_module}")
            print(f"Results will be saved with 'analysis_' prefix in test_results/")
            
            # Step 1: Generate mutants using existing generator
            print(f"\n" + "=" * 50)
            print("STEP 1: MUTANT GENERATION (Using MutantGenerator)")
            print("=" * 50)
            
            if not generator.generate_mutants():
                raise RuntimeError("Failed to generate mutants using MutantGenerator")
            
            if not generator.separate_mutants():
                raise RuntimeError("Failed to separate mutants using MutantGenerator")
            
            print(f"Mutants generated and stored in: {self.generated_mutants_dir}")
            
            # Step 2: Test mutants using existing tester
            print(f"\n" + "=" * 50)
            print("STEP 2: MUTATION TESTING (Using MutantTester)")
            print("=" * 50)
            
            # Initialize results file with analysis prefix
            calculator.initialize_results_file()
            
            print(f"Starting mutation testing for {source_module}")
            print(f"Source: {generator.source_file}")
            print(f"Tests: {generator.test_file}")
            print(f"Mutants: {generator.mutants_dir}")
            print("-" * 60)
            
            # Test original source first
            print("Testing original source code...")
            status, num_tests, num_pass, num_fail, exec_time, error_msg = tester.test_original_source()
            calculator.record_test_result(
                f"original_{source_module}.py", "original", status, 
                num_tests, num_pass, num_fail, exec_time, error_msg
            )
            
            # Test each mutant using existing tester
            mutant_files = generator.get_mutant_files()
            print(f"\nTesting {len(mutant_files)} mutants using MutantTester...")
            
            test_results = []
            
            for i, mutant_file in enumerate(mutant_files, 1):
                mutant_name = mutant_file.stem
                
                with open(mutant_file, 'r') as f:
                    mutant_content = f.read()
                
                status, num_tests, num_pass, num_fail, exec_time, error_msg = tester.test_single_mutant(
                    mutant_content, mutant_name
                )
                
                # Record result
                calculator.record_test_result(
                    mutant_file.name, "mutant", status,
                    num_tests, num_pass, num_fail, exec_time, error_msg
                )
                
                # Store for score calculation
                test_results.append((
                    mutant_file.name, "mutant", status,
                    num_tests, num_pass, num_fail, exec_time, error_msg
                ))
                
                # Show progress
                if i % 5 == 0 or i == len(mutant_files):
                    print(f"  Progress: {i}/{len(mutant_files)} mutants tested")
            
            # Step 3: Calculate mutation score using existing calculator
            print(f"\n" + "=" * 50)
            print("STEP 3: MUTATION SCORE CALCULATION (Using MutationScoreCalculator)")
            print("=" * 50)
            
            mutation_stats = calculator.calculate_mutation_score(test_results)
            
            # Generate reports using existing calculator
            calculator.generate_summary_report(mutation_stats)
            calculator.generate_final_analysis(mutation_stats)
            
            print(f"\n" + "=" * 50)
            print("STANDALONE MUTATION ANALYSIS RESULTS")
            print("=" * 50)
            print(f"Test file: {test_file.name}")
            print(f"Source module: {source_module}.py")
            print(f"Total mutants: {mutation_stats['total_mutants']}")
            print(f"Killed mutants: {mutation_stats['killed_mutants']}")
            print(f"Surviving mutants: {mutation_stats['surviving_mutants']}")
            print(f"Problematic mutants: {mutation_stats['problematic_mutants']}")
            print(f"Mutation score: {mutation_stats['mutation_score']:.1f}%")
            print(f"CSV results: {calculator.results_csv_path}")
            print(f"Summary report: {calculator.summary_path}")
            print(f"Generated mutants: {self.generated_mutants_dir}")

            # Provide interpretation
            score = mutation_stats['mutation_score']
            if score >= 85:
                print(f"EXCELLENT mutation score (≥85%) - Test suite is highly effective!")
            elif score >= 70:
                print(f"GOOD mutation score (70-84%) - Test suite is effective")
            elif score >= 50:
                print(f"MODERATE mutation score (50-69%) - Test suite needs improvement")
            else:
                print(f"POOR mutation score (<50%) - Test suite needs significant improvement")
            
            print("=" * 50)
            
            return {
                'success': True,
                'test_file': str(test_file),
                'source_module': source_module,
                'source_file': str(source_file),
                'mutation_stats': mutation_stats,
                'results_csv': str(calculator.results_csv_path),
                'summary_file': str(calculator.summary_path),
                'mutants_tested': len(mutant_files)
            }
            
        except Exception as e:
            print(f"Mutation analysis failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


def main():
    """Main entry point for the standalone mutation analyzer."""
    if len(sys.argv) != 2:
        print("Usage: python mutation_analysis/run_mutation_analysis.py <test_file_name>")
        print("\nExample:")
        print("  python mutation_analysis/run_mutation_analysis.py llm_generated_test_sample_number")
        print("  python mutation_analysis/run_mutation_analysis.py pynguin_generated_test_sample_utility")
        sys.exit(1)
    
    test_file_name = sys.argv[1]
    
    try:
        analyzer = StandaloneMutationAnalyzer()
        result = analyzer.run_mutation_analysis(test_file_name)
        
        if result['success']:
            print(f"\nMutation analysis completed successfully!")
            print(f"Results saved to: {result['results_csv']}")
            print(f"Summary saved to: {result['summary_file']}")
        else:
            print(f"\nMutation analysis failed: {result['error']}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
