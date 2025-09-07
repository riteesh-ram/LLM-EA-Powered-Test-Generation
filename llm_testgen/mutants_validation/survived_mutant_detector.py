#!/usr/bin/env python3
"""
Survived Mutant Detector

This module reads mutation test results and identifies which mutants survived
(i.e., passed all tests like the original code).
"""

import csv
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging


class SurvivedMutantDetector:
    """Detects which mutants survived from mutation test results."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the detector."""
        self.logger = logger or logging.getLogger(__name__)
    
    def get_latest_results_file(self, source_name: str, results_dir: Path) -> Optional[Path]:
        """
        Get the most recent mutation test results file for a source.
        """
        # Try multiple patterns as the file naming might vary
        patterns = [
            f"mutation_test_results_{source_name}_*.csv",
            f"mutation_results_{source_name}_*.csv", 
            f"*{source_name}*.csv"
        ]
        
        result_files = []
        for pattern in patterns:
            files = list(results_dir.glob(pattern))
            result_files.extend(files)
        
        if not result_files:
            self.logger.warning(f"No mutation test results found for {source_name} in {results_dir}")
            self.logger.warning(f"Tried patterns: {patterns}")
            # List available files for debugging
            available_files = list(results_dir.glob("*.csv"))
            self.logger.warning(f"Available CSV files: {[f.name for f in available_files]}")
            return None
        
        # Remove duplicates and sort by modification time to get the latest
        result_files = list(set(result_files))
        latest_file = max(result_files, key=lambda f: f.stat().st_mtime)
        self.logger.info(f"Using latest results: {latest_file}")
        
        return latest_file
    
    def parse_mutation_results(self, results_file: Path) -> Dict:
        """
        Parse mutation test results from CSV file.
        """
        try:
            results = {
                'original': None,
                'killed_mutants': [],
                'survived_mutants': [],
                'problematic_mutants': [],
                'total_mutants': 0
            }
            
            self.logger.info(f"Parsing mutation results from: {results_file}")
            
            with open(results_file, 'r') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    file_name = row['file_name']
                    file_type = row['file_type']
                    status = row['status']
                    
                    if file_type == 'original':
                        results['original'] = {
                            'name': file_name,
                            'status': status,
                            'num_tests': int(row['num_tests']) if row['num_tests'] else 0,
                            'num_pass': int(row['num_pass']) if row['num_pass'] else 0,
                            'num_fail': int(row['num_fail']) if row['num_fail'] else 0
                        }
                        self.logger.info(f"Original source: {file_name} - {status}")
                    
                    elif file_type == 'mutant':
                        results['total_mutants'] += 1
                        mutant_info = {
                            'name': file_name,
                            'status': status,
                            'num_tests': int(row['num_tests']) if row['num_tests'] else 0,
                            'num_pass': int(row['num_pass']) if row['num_pass'] else 0,
                            'num_fail': int(row['num_fail']) if row['num_fail'] else 0,
                            'error_msg': row.get('error_msg', '')
                        }
                        
                        if status == 'PASS' and mutant_info['num_tests'] > 0:
                            # Mutant survived (passed all tests like original)
                            results['survived_mutants'].append(mutant_info)
                            self.logger.info(f"SURVIVED: {file_name} - {status} ({mutant_info['num_pass']}/{mutant_info['num_tests']})")
                        elif status == 'FAIL' and mutant_info['num_tests'] > 0:
                            # Mutant was killed (failed some tests)
                            results['killed_mutants'].append(mutant_info)
                            self.logger.debug(f"KILLED: {file_name} - {status} ({mutant_info['num_pass']}/{mutant_info['num_tests']})")
                        else:
                            # Mutant had issues (no tests ran, errors, etc.)
                            results['problematic_mutants'].append(mutant_info)
                            self.logger.debug(f"PROBLEMATIC: {file_name} - {status} (no tests)")
            
            self.logger.info(f"Parsing complete: {len(results['survived_mutants'])} survived, "
                           f"{len(results['killed_mutants'])} killed, "
                           f"{len(results['problematic_mutants'])} problematic")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error parsing results file {results_file}: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return {}
    
    def get_survived_mutants(self, source_name: str, results_dir: Path = None) -> List[str]:
        """
        Get list of mutant filenames that survived.
        """
        if results_dir is None:
            # Look in the project root test_results directory
            results_dir = Path.cwd() / "test_results"
        
        # Ensure we have absolute path for proper resolution
        if not results_dir.is_absolute():
            results_dir = Path.cwd() / results_dir
            
        self.logger.info(f"Looking for survived mutants in: {results_dir}")
        
        # Get latest results file
        results_file = self.get_latest_results_file(source_name, results_dir)
        if not results_file:
            self.logger.warning(f"No results file found for {source_name}")
            return []
        
        # Parse results
        results = self.parse_mutation_results(results_file)
        if not results:
            self.logger.warning(f"Failed to parse results from {results_file}")
            return []
        
        # Extract survived mutant names
        survived_names = [mutant['name'] for mutant in results['survived_mutants']]
        
        self.logger.info(f"Found {len(survived_names)} survived mutants: {survived_names}")
        return survived_names
    
    def get_mutation_summary(self, source_name: str, results_dir: Path = None) -> Dict:
        """
        Get complete mutation testing summary.
        """
        if results_dir is None:
            results_dir = Path("test_results")
        
        results_file = self.get_latest_results_file(source_name, results_dir)
        if not results_file:
            return {}
        
        results = self.parse_mutation_results(results_file)
        if not results:
            return {}
        
        # Calculate mutation score
        killed_count = len(results['killed_mutants'])
        total_valid = killed_count + len(results['survived_mutants'])
        mutation_score = (killed_count / total_valid * 100) if total_valid > 0 else 0
        
        summary = {
            'source_name': source_name,
            'results_file': str(results_file),
            'total_mutants': results['total_mutants'],
            'killed_mutants': killed_count,
            'survived_mutants': len(results['survived_mutants']),
            'problematic_mutants': len(results['problematic_mutants']),
            'mutation_score': round(mutation_score, 1),
            'survived_mutant_names': [m['name'] for m in results['survived_mutants']],
            'original_test_status': results['original']['status'] if results['original'] else 'Unknown'
        }
        
        return summary


def main():
    """Demo the survived mutant detector."""
    logging.basicConfig(level=logging.INFO)
    
    detector = SurvivedMutantDetector()
    
    # Test with sample_number
    source_name = "sample_number"
    summary = detector.get_mutation_summary(source_name)
    
    if summary:
        print("=" * 60)
        print("MUTATION TESTING SUMMARY")
        print("=" * 60)
        print(f"Source: {summary['source_name']}")
        print(f"Results file: {summary['results_file']}")
        print(f"Total mutants: {summary['total_mutants']}")
        print(f"Killed: {summary['killed_mutants']}")
        print(f"Survived: {summary['survived_mutants']}")
        print(f"Problematic: {summary['problematic_mutants']}")
        print(f"Mutation score: {summary['mutation_score']}%")
        print(f"Original tests: {summary['original_test_status']}")
        
        if summary['survived_mutant_names']:
            print(f"\nSURVIVED MUTANTS TO TARGET:")
            for mutant in summary['survived_mutant_names']:
                print(f"  - {mutant}")
        else:
            print(f"\nNO SURVIVING MUTANTS - 100% mutation score!")
    else:
        print("Could not get mutation summary")


if __name__ == "__main__":
    main()
