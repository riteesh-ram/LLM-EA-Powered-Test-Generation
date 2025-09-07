#!/usr/bin/env python3
"""
Mutation Score Calculator Module

This module handles calculation and reporting of mutation scores.
Single responsibility: Calculate mutation scores and generate reports.
"""

import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging


class MutationScoreCalculator:
    """Handles mutation score calculation and reporting."""
    
    def __init__(self, module_name: str, logger: Optional[logging.Logger] = None):
        """
        Initialize mutation score calculator.
        """
        self.module_name = module_name
        self.logger = logger or logging.getLogger(__name__)
        
        # Define paths - save results in project root test_results directory
        self.workspace_root = Path.cwd()  # This should be llm_testgen when running the pipeline
        self.source_dir = self.workspace_root / "tests" / "source"
        self.test_dir = self.workspace_root / "tests" / "test_suites"
        self.mutants_dir = self.workspace_root / "mutants_validation" / "generated_mutants"
        self.results_dir = self.workspace_root / "test_results"  # Save results in llm_testgen/test_results
        
        # File paths
        self.source_file = self.source_dir / f"{module_name}.py"
        self.test_file = self.test_dir / f"llm_generated_test_{module_name}.py"
        
        # Ensure results directory exists
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate timestamp for this run
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results_csv_path = self.results_dir / f"mutation_test_results_{module_name}_{self.timestamp}.csv"
        self.summary_path = self.results_dir / f"mutation_summary_{module_name}_{self.timestamp}.txt"
    
    def initialize_results_file(self) -> None:
        """Initialize the CSV results file with headers."""
        with open(self.results_csv_path, 'w') as csv_file:
            csv_file.write("file_name,file_type,status,num_tests,num_pass,num_fail,execution_time,error_msg\n")
    
    def record_test_result(self, file_name: str, file_type: str, 
                          status: str, num_tests: int, num_pass: int, 
                          num_fail: int, exec_time: str, error_msg: str = "") -> None:
        """
        Record a single test result to the CSV file.
        """
        with open(self.results_csv_path, 'a') as csv_file:
            csv_file.write(f"{file_name},{file_type},{status},{num_tests},{num_pass},{num_fail},{exec_time},{error_msg}\n")
    
    def calculate_mutation_score(self, test_results: List[Tuple[str, str, str, int, int, int, str, str]]) -> Dict[str, any]:
        """
        Calculate mutation score from test results.
        """
        killed_mutants = 0
        surviving_mutants = 0
        problematic_mutants = 0
        
        # Process results (skip original source result)
        for result in test_results:
            file_name, file_type, status, num_tests, num_pass, num_fail, exec_time, error_msg = result
            
            # Skip original source file
            if file_type == "original":
                continue
            
            # Count killed vs surviving mutants
            # ALL TESTS PASS = mutant SURVIVED (test cases couldn't detect the mutation - BAD)
            # SOME/ALL TESTS FAIL = mutant KILLED (test cases detected the mutation - GOOD)
            # 0 tests executed = problematic mutant (runtime error)
            # TIMEOUT/ERROR = problematic mutant
            if status == "PASS" and num_tests > 0:
                surviving_mutants += 1  # All tests passed - mutant survived detection
            elif status == "FAIL":
                # Check if it's a problematic mutant (0 tests executed = runtime error)
                if num_tests == 0:
                    problematic_mutants += 1  # No tests executed - problematic
                else:
                    killed_mutants += 1  # Some/all tests failed - mutant was detected and killed
            else:  # TIMEOUT or ERROR
                problematic_mutants += 1
        
        # Calculate mutation score
        total_mutants = killed_mutants + surviving_mutants + problematic_mutants
        valid_mutants = total_mutants - problematic_mutants  # Exclude problematic from calculation
        
        # Mutation Score = killed_mutants / (total_mutants - problematic_mutants)
        mutation_score = (killed_mutants / valid_mutants * 100) if valid_mutants > 0 else 0
        
        return {
            'total_mutants': total_mutants,
            'killed_mutants': killed_mutants,
            'surviving_mutants': surviving_mutants,
            'problematic_mutants': problematic_mutants,
            'valid_mutants': valid_mutants,
            'mutation_score': mutation_score,
            'results_file': self.results_csv_path,
            'summary_file': self.summary_path
        }
    
    def generate_summary_report(self, mutation_stats: Dict[str, any]) -> None:
        """
        Generate a detailed summary report.
        """
        # Print summary to console
        self.logger.info("\\n" + "=" * 60)
        self.logger.info("MUTATION TESTING SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Source file: {self.module_name}.py")
        self.logger.info(f"Total mutants: {mutation_stats['total_mutants']}")
        self.logger.info(f"Killed mutants: {mutation_stats['killed_mutants']}")
        self.logger.info(f"Surviving mutants: {mutation_stats['surviving_mutants']}")
        if mutation_stats['problematic_mutants'] > 0:
            self.logger.info(f"Problematic mutants: {mutation_stats['problematic_mutants']}")
        self.logger.info(f"Mutation score: {mutation_stats['mutation_score']:.1f}%")
        self.logger.info(f"Results saved to: {self.results_csv_path}")
        
        # Create summary file
        with open(self.summary_path, 'w') as f:
            f.write(f"Mutation Testing Summary for {self.module_name}\\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
            f.write(f"Source file: {self.source_file}\\n")
            f.write(f"Test file: {self.test_file}\\n")
            f.write(f"Mutants directory: {self.mutants_dir}\\n\\n")
            f.write(f"Total mutants tested: {mutation_stats['total_mutants']}\\n")
            f.write(f"Killed mutants: {mutation_stats['killed_mutants']}\\n")
            f.write(f"Surviving mutants: {mutation_stats['surviving_mutants']}\\n")
            if mutation_stats['problematic_mutants'] > 0:
                f.write(f"Problematic mutants: {mutation_stats['problematic_mutants']}\\n")
            f.write(f"Mutation score: {mutation_stats['mutation_score']:.1f}%\\n")
            f.write(f"\\nDetailed results: {self.results_csv_path}\\n")
    
    def generate_final_analysis(self, mutation_stats: Dict[str, any]) -> None:
        """
        Generate final analysis and recommendations.
        """
        self.logger.info("\\n" + "=" * 60)
        self.logger.info("FINAL MUTATION SCORE ANALYSIS")
        self.logger.info("=" * 60)
        
        # Print final summary
        self.logger.info(f"Mutation testing pipeline completed successfully!")
        
        # Show mutation score
        final_score = mutation_stats['mutation_score']
        self.logger.info(f"Mutation Score: {final_score:.1f}%")
        self.logger.info(f"Results: {mutation_stats['results_file']}")
        self.logger.info(f"Summary: {mutation_stats['summary_file']}")
        
        # Provide interpretation based on score
        if final_score >= 85:
            self.logger.info("EXCELLENT mutation score (≥85%)")
        elif final_score >= 70:
            self.logger.info("GOOD mutation score (70-84%)")
        elif final_score >= 50:
            self.logger.info("MODERATE mutation score (50-69%) - needs improvement")
        else:
            self.logger.info("POOR mutation score (<50%) - significant improvement needed")
    
    def read_results_from_csv(self) -> List[Tuple[str, str, str, int, int, int, str, str]]:
        #Read test results from CSV file.

        results = []
        try:
            with open(self.results_csv_path, 'r') as csv_file:
                reader = csv.reader(csv_file)
                next(reader)  # Skip header
                
                for row in reader:
                    if len(row) >= 7:
                        file_name, file_type, status, num_tests, num_pass, num_fail, exec_time = row[:7]
                        error_msg = row[7] if len(row) > 7 else ""
                        results.append((
                            file_name, file_type, status,
                            int(num_tests), int(num_pass), int(num_fail),
                            exec_time, error_msg
                        ))
        except Exception as e:
            self.logger.error(f"Error reading results from CSV: {e}")
        
        return results
