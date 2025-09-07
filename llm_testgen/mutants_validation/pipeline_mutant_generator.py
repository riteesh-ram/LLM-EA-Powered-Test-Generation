#!/usr/bin/env python3
"""
Mutation Testing Pipeline - Main Controller

This script orchestrates the mutation testing pipeline:
1. Generates mutants using MutPy
2. Tests mutants against test suite  
3. Calculates mutation score

Uses modular design with separate components for each responsibility.
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import List, Tuple, Dict

# Add current directory to path for local imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import our modular components
from mutant_generator import MutantGenerator
from mutant_tester import MutantTester
from mutation_score_calculator import MutationScoreCalculator
from survived_mutant_detector import SurvivedMutantDetector

# Optional imports for survivor killer
try:
    from enhanced_survivor_killer import EnhancedSurvivorKiller
    from enhanced_survivor_killer_integrated import integrate_killer_tests_into_pipeline
    from final_survivor_killer import integrate_final_killer_into_pipeline
except ImportError:
    pass  # These are optional features


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def run_demo_analysis(original_file: Path, test_file: Path, mutants_dir: Path, survived_mutants: List[str], logger: logging.Logger) -> Dict:
    """
    Run demo analysis showing what the enhanced survivor killer would do.
    
    Args:
        original_file: Path to original source file
        test_file: Path to existing test file
        mutants_dir: Directory containing mutant files
        survived_mutants: List of surviving mutant filenames
        logger: Logger instance
        
    Returns:
        Dictionary with demo analysis results
    """
    try:
        from mutant_diff_analyzer import MutantDiffAnalyzer
        
        logger.info(f"Source file: {original_file}")
        logger.info(f"Test file: {test_file}")
        logger.info(f"Mutants directory: {mutants_dir}")
        
        # Verify files exist
        if not original_file.exists():
            return {'status': 'error', 'error': f'Source file not found: {original_file}'}
        if not test_file.exists():
            return {'status': 'error', 'error': f'Test file not found: {test_file}'}
        
        # Analyze each surviving mutant
        analyzer = MutantDiffAnalyzer()
        analyses = []
        
        logger.info(f"\nAnalyzing {len(survived_mutants)} surviving mutants:")
        
        for mutant_name in survived_mutants:
            mutant_file = mutants_dir / mutant_name
            if mutant_file.exists():
                analysis = analyzer.analyze_mutant_diff(original_file, mutant_file)
                analyses.append(analysis)
                
                # Show analysis results
                logger.info(f"\n {mutant_name}:")
                if 'changes' in analysis:
                    for change in analysis['changes']:
                        line_num = change.get('line_number')
                        original = change.get('original', '')
                        mutated = change.get('mutated', '')
                        logger.info(f"    Line {line_num}: '{original}' → '{mutated}'")
                else:
                    logger.info(f"    No changes detected")
        
        # Generate what the prompt would look like
        logger.info(f"\nGenerated mutation analysis for {len(analyses)} mutants")
        logger.info(f"Prompt would include:")
        logger.info(f"   - Source code upload: {original_file.name}")
        logger.info(f"   - Test file upload: {test_file.name}")
        logger.info(f"   - Detailed mutation analysis for each surviving mutant")
        logger.info(f"   - Style-aware test generation instructions")
        
        # Show sample of what would be generated
        logger.info(f"\nSample prompt content:")
        logger.info(f"   'Generate new test methods that kill the following surviving mutants:'")
        for i, analysis in enumerate(analyses[:2], 1):  # Show first 2
            mutant_name = analysis.get('mutant_file', f'mutant_{i}')
            logger.info(f"   'MUTANT {i}: {mutant_name}'")
            if 'changes' in analysis:
                for change in analysis['changes'][:1]:  # Show first change
                    line_num = change.get('line_number')
                    original = change.get('original', '')
                    mutated = change.get('mutated', '')
                    logger.info(f"   '  Line {line_num}: {original} → {mutated}'")
        
        if len(analyses) > 2:
            logger.info(f"   ... and {len(analyses) - 2} more mutants")
        
        return {
            'status': 'success',
            'analysis': f'Demo analysis completed for {len(analyses)} surviving mutants',
            'mutant_analyses': analyses,
            'files_analyzed': {
                'source': str(original_file),
                'test': str(test_file),
                'mutants': len(analyses)
            }
        }
        
    except Exception as e:
        logger.error(f"Error in demo analysis: {e}")
        return {'status': 'error', 'error': str(e)}


def run_mutation_testing_pipeline(module_name: str, csv_report: str, skip_generation: bool, run_survivor_killer: bool, logger: logging.Logger):
    """
    Run the complete mutation testing pipeline.
    
    Args:
        module_name: Name of the module to test
        csv_report: CSV file for mutation types
        skip_generation: Whether to skip mutant generation
        run_survivor_killer: Whether to run survivor killer for surviving mutants
        logger: Logger instance
        
    Returns:
        Dictionary with mutation testing results
    """
    # Initialize components
    generator = MutantGenerator(module_name, logger)
    tester = MutantTester(module_name, logger)
    calculator = MutationScoreCalculator(module_name, logger)
    detector = SurvivedMutantDetector(logger)
    
    # Initialize survivor killer only if needed
    survivor_killer = None
    demo_mode = False
    if run_survivor_killer:
        try:
            from survivor_killer_integrated import SurvivorKillerIntegrated
            survivor_killer = SurvivorKillerIntegrated()
            logger.info("Integrated survivor killer initialized with existing chat session")
        except Exception as e:
            logger.warning(f"Failed to initialize survivor killer: {e}")
            logger.warning("Running in DEMO mode - check GEMINI_API_KEY configuration")
            demo_mode = True
    
    # Step 1: Generate mutants (if not skipped)
    if not skip_generation:
        logger.info("=" * 60)
        logger.info("STEP 1: MUTANT GENERATION")
        logger.info("=" * 60)
        
        # Generate mutants using MutPy
        if not generator.generate_mutants():
            logger.error("Failed to generate mutants")
            return None
        
        # Separate individual mutants
        if not generator.separate_mutants(csv_report):
            logger.error("Failed to separate mutants")
            return None
    else:
        logger.info("Skipping mutant generation (--skip-generation flag)")
    
    # Step 2: Test mutants
    logger.info("\n" + "=" * 60)
    logger.info("STEP 2: MUTATION TESTING")
    logger.info("=" * 60)
    
    # Initialize results file
    calculator.initialize_results_file()
    
    logger.info(f"Starting mutation testing for {module_name}")
    logger.info(f"Source: {generator.source_file}")
    logger.info(f"Tests: {generator.test_file}")
    logger.info(f"Mutants: {generator.mutants_dir}")
    logger.info("-" * 60)
    
    # Test original source first
    logger.info("Testing original source code...")
    status, num_tests, num_pass, num_fail, exec_time, error_msg = tester.test_original_source()
    calculator.record_test_result(
        f"original_{module_name}.py", "original", status, 
        num_tests, num_pass, num_fail, exec_time, error_msg
    )
    
    # Test each mutant
    mutant_files = generator.get_mutant_files()
    logger.info(f"\nTesting {len(mutant_files)} mutants...")
    
    test_results = []
    
    for mutant_file in mutant_files:
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
    
    # Step 3: Calculate mutation score
    mutation_stats = calculator.calculate_mutation_score(test_results)
    
    # Generate reports
    calculator.generate_summary_report(mutation_stats)
    calculator.generate_final_analysis(mutation_stats)
    
    # Step 4: Run integrated survivor killer (if requested and there are surviving mutants)
    if run_survivor_killer and mutation_stats['surviving_mutants'] > 0:
        logger.info("\n" + "=" * 60)
        logger.info("STEP 4: INTEGRATED SURVIVOR KILLER")
        logger.info("=" * 60)
        
        # Get survived mutants from latest results
        survived_mutants = detector.get_survived_mutants(module_name)
        
        if survived_mutants:
            logger.info(f"Found {len(survived_mutants)} surviving mutants: {survived_mutants}")
            
            # Set up paths - use absolute path for mutants directory
            mutants_dir = Path(__file__).parent / "generated_mutants"
            logger.info(f"Mutants directory: {mutants_dir}")
            logger.info(f"Mutants directory exists: {mutants_dir.exists()}")
            if mutants_dir.exists():
                mutants_count = len(list(mutants_dir.glob("mutant_*.py")))
                logger.info(f"Found {mutants_count} mutant files in directory")
            
            if demo_mode:
                # Run demo analysis without LLM call
                logger.info("Running in DEMO mode - no LLM available")
                result = {
                    'status': 'error',
                    'error': 'LLM not available for killer test generation'
                }
            else:
                # Run integrated survivor killer with LLM and test suite manager
                logger.info("Running integrated survivor killer with test suite manager")
                result = survivor_killer.analyze_and_kill_survivors(
                    module_name, survived_mutants, mutants_dir
                )
            
            if result['status'] == 'success':
                logger.info("Integrated survivor killer completed successfully")
                
                # Save summary of results
                mutation_stats['killer_tests_generated'] = True
                mutation_stats['killer_test_file'] = result.get('killer_test_file')
                mutation_stats['mutants_analyzed'] = result['total_mutants_analyzed']
                mutation_stats['killer_tests_working'] = result.get('killer_tests_working', False)
                
                # Get test results
                test_results = result.get('test_results', {})
                mutation_stats['mutants_killed_by_new_tests'] = len(test_results.get('mutants_killed', []))
                mutation_stats['mutants_still_surviving_after_killer'] = len(test_results.get('mutants_still_surviving', []))
                
                # Log detailed results
                logger.info(f"Integrated Killer Tests Results:")
                logger.info(f"   - Generated killer test file: {result.get('killer_test_file')}")
                logger.info(f"   - Mutants analyzed: {result['total_mutants_analyzed']}")
                logger.info(f"   - Killer tests working: {result.get('killer_tests_working', False)}")
                logger.info(f"   - Mutants killed by new tests: {len(test_results.get('mutants_killed', []))}")
                logger.info(f"   - Mutants still surviving: {len(test_results.get('mutants_still_surviving', []))}")
                
                if test_results.get('mutants_killed'):
                    logger.info(f"   Killed mutants: {test_results['mutants_killed']}")
                
                if test_results.get('mutants_still_surviving'):
                    logger.warning(f"   Still surviving: {test_results['mutants_still_surviving']}")
                
                if len(test_results.get('mutants_still_surviving', [])) == 0:
                    logger.info("All surviving mutants have been killed by the new tests!")
                    
                    # Check if merge was successful
                    merge_results = test_results.get('merge_results', {})
                    if merge_results.get('success'):
                        logger.info("\n" + "=" * 60)
                        logger.info("STEP 5: FINAL MUTATION TESTING WITH MERGED TESTS")
                        logger.info("=" * 60)
                        
                        # Run final mutation testing with merged test suite
                        merged_file = merge_results['merged_file']
                        logger.info(f"Testing with merged file: {merged_file}")
                        
                        # Initialize new calculator for final results
                        final_calculator = MutationScoreCalculator(module_name, logger)
                        final_calculator.initialize_results_file()
                        
                        # Initialize tester with merged test file - use the module name and update test file
                        final_tester = MutantTester(module_name, logger)
                        final_tester.test_file = Path(merged_file)  # Update to use merged test file
                        
                        # Test original source with merged tests
                        logger.info("Testing original source with merged test suite...")
                        status, num_tests, num_pass, num_fail, exec_time, error_msg = final_tester.test_original_source()
                        final_calculator.record_test_result(
                            f"original_{module_name}.py", "original", status, 
                            num_tests, num_pass, num_fail, exec_time, error_msg
                        )
                        
                        # Test all mutants with merged test suite
                        logger.info(f"Testing {len(mutant_files)} mutants with merged test suite...")
                        final_test_results = []
                        
                        for mutant_file in mutant_files:
                            mutant_name = mutant_file.stem
                            
                            with open(mutant_file, 'r') as f:
                                mutant_content = f.read()
                            
                            status, num_tests, num_pass, num_fail, exec_time, error_msg = final_tester.test_single_mutant(
                                mutant_content, mutant_name
                            )
                            
                            final_calculator.record_test_result(
                                mutant_file.name, "mutant", status,
                                num_tests, num_pass, num_fail, exec_time, error_msg
                            )
                            
                            final_test_results.append((
                                mutant_file.name, "mutant", status,
                                num_tests, num_pass, num_fail, exec_time, error_msg
                            ))
                        
                        # Calculate final mutation score
                        final_mutation_stats = final_calculator.calculate_mutation_score(final_test_results)
                        final_calculator.generate_summary_report(final_mutation_stats)
                        final_calculator.generate_final_analysis(final_mutation_stats)
                        
                        logger.info("\nFINAL RESULTS WITH MERGED TEST SUITE:")
                        logger.info(f"Final Mutation Score: {final_mutation_stats['mutation_score']:.1f}%")
                        logger.info(f"Final Results: {final_calculator.results_csv_path}")
                        logger.info(f"Final Summary: {final_calculator.summary_path}")
                        
                        if final_mutation_stats['mutation_score'] == 100.0:
                            logger.info("PERFECT SCORE! All mutants killed with merged test suite!")
                        
                    else:
                        logger.warning("Merge failed, final testing skipped")
                else:
                    logger.warning("Some mutants still surviving, merge and final testing skipped")
                    
            else:
                logger.error(f"Integrated survivor killer failed: {result.get('error', 'Unknown error')}")
                mutation_stats['killer_tests_generated'] = False
                mutation_stats['killer_tests_working'] = False
        else:
            logger.info("No surviving mutants found in latest results")
            mutation_stats['killer_tests_generated'] = False
            
    elif run_survivor_killer and mutation_stats['surviving_mutants'] == 0:
        logger.info("\nNo surviving mutants found - no killer tests needed!")
        mutation_stats['killer_tests_generated'] = False
    else:
        mutation_stats['killer_tests_generated'] = False
    
    return mutation_stats


def main():
    """Main function for mutation testing pipeline."""
    parser = argparse.ArgumentParser(
        description="Mutation testing pipeline: Generate mutants, test them, and calculate mutation score"
    )
    parser.add_argument(
        "module_name", 
        help="Name of the module to generate mutants for (e.g., sample_number)"
    )
    parser.add_argument(
        "--csv-report", 
        default="mutation_types_report.csv",
        help="CSV file to record mutation types (default: mutation_types_report.csv)"
    )
    parser.add_argument(
        "--skip-generation",
        action="store_true",
        help="Skip mutant generation and only run testing/scoring (assumes mutants already exist)"
    )
    parser.add_argument(
        "--survivor-killer",
        action="store_true",
        help="Run MuTAP-style survivor killer to generate tests for surviving mutants"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging()
    
    # Validate CSV file extension
    if not args.csv_report.endswith('.csv'):
        logger.error("Error: The report file should be a CSV")
        sys.exit(1)
    
    logger.info(f"Starting mutation testing pipeline for module: {args.module_name}")
    
    try:
        # Run the mutation testing pipeline
        results = run_mutation_testing_pipeline(
            args.module_name, args.csv_report, args.skip_generation, args.survivor_killer, logger
        )
        
        if results is None:
            logger.error("Mutation testing pipeline failed")
            sys.exit(1)
        
        logger.info("\nMutation testing pipeline completed successfully!")
        
    except Exception as e:
        logger.error(f"Failed to run mutation testing pipeline: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
