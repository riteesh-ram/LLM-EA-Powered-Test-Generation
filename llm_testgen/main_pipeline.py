#!/usr/bin/env python3
"""
Main pipeline for LLM test generation with evolutionary algorithms and mutation testing.

This module orchestrates the entire test generation process:
1. Initial test suite generation using LLMs
2. Test normalization for Pynguin compatibility 
3. Evolutionary algorithm integration for test improvement
4. Population management and fitness evaluation
5. Pynguin execution with dynamic population sizing
6. Test suite merging (LLM + Pynguin)
7. Automated test repair
8. mutation testing pipeline
"""

import sys
import os
import subprocess
import logging
import shutil
from pathlib import Path
from datetime import datetime

# Disable Python caching globally
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
os.environ['PYTHONPYCACHEPREFIX'] = '/tmp/disabled_pycache'
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from evolutionary_algo_integration.normalizer import generate_seed_file, ExtractionConfig
from initial_test_suite_generation.analysis.test_pipeline import TestGenerationPipeline
from initial_test_suite_generation.repair.test_suite_manager import TestSuiteManager
from initial_test_suite_generation.generation.config import MAX_REPAIR_ATTEMPTS
from evolutionary_algo_integration.llm_ea_tests.test_merger import TestSuiteMerger
from pipeline_config import PipelineConfig
from source_analyzer import SourceAnalyzer

def create_dynamic_pipeline_config(module_name: str) -> PipelineConfig:
    #Create a pipeline configuration with dynamically extracted function names.
    # Construct the source file path
    source_file = Path("tests/source") / f"{module_name}.py"
    
    if not source_file.exists():
        logging.warning(f"Source file {source_file} not found. Using default configuration.")
        return PipelineConfig(module_name)
    
    try:
        # Analyze the source file to extract function names
        analyzer = SourceAnalyzer(source_file)
        target_functions = analyzer.get_target_functions_for_testing()
        
        if not target_functions:
            logging.warning(f"No testable functions found in {source_file}. Using module name as function name.")
            return PipelineConfig(module_name)
        
        logging.info(f"Source Analysis for {module_name}:")
        logging.info(f"   • Target functions: {target_functions}")
        
        # Log complexity metrics
        complexity = analyzer.analyze_complexity()
        logging.info(f"   • Complexity: {complexity['functions']} functions, "
                    f"{complexity['classes']} classes, "
                    f"{complexity['lines_of_code']} LOC")
        
        # Create configuration with extracted function names
        config = PipelineConfig(
            module_name=module_name,
            function_names=target_functions
        )
        
        return config
        
    except Exception as e:
        logging.error(f"Failed to analyze source file {source_file}: {e}")
        logging.warning("Falling back to default configuration")
        return PipelineConfig(module_name)


def cleanup_cache_directories():
    """
    Clean up cache directories to prevent space consumption and ensure clean execution.
    """
    print("Cleaning up cache directories...")
    
    workspace_root = Path.cwd()
    
    # Run the comprehensive cache cleanup script
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, "cleanup_all_caches.py"],
            capture_output=True,
            text=True,
            cwd=str(workspace_root)
        )
        
        if result.returncode == 0:
            print("Comprehensive cache cleanup completed")
            # Also print the output to show what was cleaned
            output_lines = result.stdout.strip().split('\n')
            for line in output_lines[-3:]:  # Show last 3 lines (summary)
                if line.strip():
                    print(f"   {line}")
        else:
            print(f"Cache cleanup script failed: {result.stderr}")
    except Exception as e:
        print(f"Could not run cache cleanup script: {e}")
    
    # Fallback: manual cleanup of critical directories
    cache_patterns = [
        "**/__pycache__", 
        "**/.pytest_cache", 
        "**/tests/**/__pycache__",
        "**/mutants_validation/__pycache__",
        "**/temp_test_dir/.pytest_cache"
    ]
    
    removed_dirs = 0
    
    for pattern in cache_patterns:
        for cache_dir in workspace_root.glob(pattern):
            if cache_dir.is_dir():
                try:
                    # Skip virtual environment directories
                    if any(venv in str(cache_dir) for venv in ['myvenv', 'mutpy_env', 'my_pynguin_venv']):
                        continue
                        
                    shutil.rmtree(cache_dir)
                    removed_dirs += 1
                except Exception:
                    pass  # Ignore errors in fallback cleanup
    
    if removed_dirs > 0:
        print(f"Fallback cleanup removed {removed_dirs} additional cache directories")
    
    print("Cache cleanup completed")


def run_mutation_testing_pipeline(config: PipelineConfig):
    """Run our complete mutation testing pipeline using mutpy_env."""
    logging.info("=" * 80)
    logging.info("STAGE 6: COMPLETE MUTATION TESTING PIPELINE")
    logging.info("=" * 80)
    logging.info(f"Module: {config.module_name}")
    
    try:
        # Get mutpy_env python path
        mutpy_env_path = Path(__file__).parent / "mutants_validation" / "mutpy_env" / "bin" / "python3"
        
        logging.info("Mutation testing environment verification:")
        logging.info(f"  - MutPy environment path: {mutpy_env_path}")
        
        if not mutpy_env_path.exists():
            raise FileNotFoundError(f"MutPy environment not found: {mutpy_env_path}")
        
        logging.info("✓ MutPy environment verified")
        
        # Verify that merged test suite exists
        merged_test_file = Path(config.tests_dir) / f"llm_generated_test_{config.module_name}.py"
        logging.info(f"  - Merged test file: {merged_test_file}")
        
        if not merged_test_file.exists():
            logging.error(f"Merged test suite not found: {merged_test_file}")
            return {
                'success': False,
                'error': f"Merged test suite not found: {merged_test_file}"
            }
        
        logging.info("✓ Merged test suite verified")
        
        # Log test file details
        file_size = merged_test_file.stat().st_size
        with open(merged_test_file, 'r') as f:
            content = f.read()
            line_count = len(content.splitlines())
        
        logging.info(f"Test suite details:")
        logging.info(f"  - Size: {file_size} bytes")
        logging.info(f"  - Lines: {line_count}")
        
        # Step 1: Run complete mutation pipeline with integrated survivor killer
        logging.info("Starting complete mutation pipeline with integrated survivor killer...")
        
        mutation_pipeline_script = Path(__file__).parent / "mutants_validation" / "pipeline_mutant_generator.py"
        logging.info(f"  - Pipeline script: {mutation_pipeline_script}")
        
        # Build command with survivor killer enabled
        cmd = [
            str(mutpy_env_path), 
            str(mutation_pipeline_script), 
            config.module_name,
            "--survivor-killer"  # Enable integrated survivor killer
        ]
        
        logging.info("Mutation testing command:")
        logging.info(f"Command: {' '.join(cmd)}")
        logging.info(f"Working directory: {Path(__file__).parent}")
        
        # Set environment for mutpy_env with cache disabling
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(__file__).parent)
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        env['PYTHONPYCACHEPREFIX'] = '/tmp/disabled_pycache'
        env['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
        
        logging.info("Environment variables:")
        logging.info(f"  - PYTHONPATH: {env['PYTHONPATH']}")
        
        logging.info("Starting mutation testing execution...")
        result = run_subprocess_with_comprehensive_logging(
            cmd,
            "MUTATION_TESTING",
            cwd=str(Path(__file__).parent),
            timeout=900,  # 15 minutes timeout for complete pipeline
            env=env
        )
        
        if result.returncode == 0:
            logging.info("=" * 40)
            logging.info("MUTATION TESTING PIPELINE SUCCESSFUL")
            logging.info("=" * 40)
            
            # Parse results from output
            mutation_score = "Unknown"
            final_mutation_score = "Unknown"
            surviving_mutants = 0
            killer_tests_generated = False
            perfect_score_achieved = False
            
            output_lines = result.stdout.split('\n')
            logging.info("Parsing mutation testing results...")
            
            for line in output_lines:
                # Parse initial mutation score
                if "Mutation Score:" in line and "Final" not in line:
                    mutation_score = line.split("Mutation Score:")[1].strip()
                    logging.info(f"  - Found initial mutation score: {mutation_score}")
                # Parse final mutation score
                elif "Final Mutation Score:" in line:
                    final_mutation_score = line.split("Final Mutation Score:")[1].strip()
                    logging.info(f"  - Found final mutation score: {final_mutation_score}")
                    if "100.0%" in final_mutation_score:
                        perfect_score_achieved = True
                        logging.info("  - Perfect score detected!")
                # Parse surviving mutants count
                elif "surviving mutants" in line.lower():
                    import re
                    numbers = re.findall(r'\d+', line)
                    if numbers:
                        surviving_mutants = int(numbers[0])
                        logging.info(f"  - Found surviving mutants count: {surviving_mutants}")
                # Check if killer tests were generated
                elif "Integrated survivor killer completed successfully" in line:
                    killer_tests_generated = True
                    logging.info("  - Killer tests generation detected")
                elif "PERFECT SCORE! All mutants killed" in line:
                    perfect_score_achieved = True
                    logging.info("  - Perfect score achievement detected")
            
            # Log comprehensive results
            logging.info("=" * 60)
            logging.info("COMPLETE MUTATION TESTING RESULTS")
            logging.info("=" * 60)
            logging.info(f"Initial Mutation Score: {mutation_score}")
            logging.info(f"Final Mutation Score: {final_mutation_score}")
            logging.info(f"Surviving Mutants: {surviving_mutants}")
            logging.info(f"Killer Tests Generated: {'Yes' if killer_tests_generated else 'No'}")
            logging.info(f"Perfect Score Achieved: {'Yes' if perfect_score_achieved else 'No'}")
            
            # Find the latest mutation results CSV file
            results_dir = Path(__file__).parent / "mutants_validation" / "test_results"
            logging.info(f"Looking for results in: {results_dir}")
            
            mutation_csv_files = list(results_dir.glob(f"mutation_test_results_{config.module_name}_*.csv"))
            latest_csv = None
            if mutation_csv_files:
                latest_csv = max(mutation_csv_files, key=lambda f: f.stat().st_mtime)
                logging.info(f"Latest Results CSV: {latest_csv}")
                
                # Log CSV file details
                if latest_csv.exists():
                    csv_size = latest_csv.stat().st_size
                    logging.info(f"  - CSV size: {csv_size} bytes")
                    
                    # Read and log first few lines of CSV
                    try:
                        with open(latest_csv, 'r') as f:
                            csv_lines = f.readlines()
                        logging.info(f"  - CSV lines: {len(csv_lines)}")
                        logging.info("CSV preview (first 5 lines):")
                        for i, line in enumerate(csv_lines[:5], 1):
                            logging.info(f"    {i}: {line.strip()}")
                    except Exception as e:
                        logging.warning(f"Could not read CSV details: {e}")
            else:
                logging.warning("No mutation results CSV files found")
            
            logging.info("=" * 60)
            logging.info("STAGE 6 COMPLETED SUCCESSFULLY")
            logging.info("=" * 60)
            
            return {
                'success': True,
                'initial_mutation_score': mutation_score,
                'final_mutation_score': final_mutation_score,
                'surviving_mutants': surviving_mutants,
                'killer_tests_generated': killer_tests_generated,
                'perfect_score_achieved': perfect_score_achieved,
                'pipeline_output': result.stdout,
                'results_csv': str(latest_csv) if latest_csv else None,
                'merged_test_file': str(merged_test_file)
            }
        else:
            logging.error("=" * 40)
            logging.error("STAGE 6 FAILED - MUTATION TESTING ERROR")
            logging.error("=" * 40)
            logging.error(f"Complete mutation pipeline failed with return code {result.returncode}")
            return {
                'success': False,
                'error': f"Complete mutation pipeline failed with code {result.returncode}",
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
    except subprocess.TimeoutExpired:
        logging.error("=" * 40)
        logging.error("STAGE 6 FAILED - TIMEOUT")
        logging.error("=" * 40)
        logging.error("Complete mutation testing pipeline timed out")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logging.error("=" * 40)
        logging.error("STAGE 6 FAILED - EXCEPTION")
        logging.error("=" * 40)
        logging.error(f"Error during mutation testing pipeline: {e}")
        import traceback
        logging.error("Full traceback:")
        for line in traceback.format_exc().splitlines():
            logging.error(f"  {line}")
        logging.error("=" * 40)
        return {'success': False, 'error': str(e)}


# Configure logging
def setup_logging(module_name: str):
    """Setup comprehensive logging for the entire pipeline."""
    # Create logs directory directly under llm_testgen folder
    log_dir = Path(__file__).parent / "pipeline_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"complete_pipeline_{module_name}_{timestamp}.log"
    
    # Clear any existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # Create comprehensive logging configuration
    logging.basicConfig(
        level=logging.DEBUG,  # Capture all levels
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, mode='w', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ],
        force=True
    )
    
    # Set all loggers to DEBUG level to capture everything
    logging.getLogger().setLevel(logging.DEBUG)
    
    logging.info("=" * 80)
    logging.info("COMPLETE PIPELINE AUDIT LOG STARTED")
    logging.info("=" * 80)
    logging.info(f"Module: {module_name}")
    logging.info(f"Timestamp: {datetime.now().isoformat()}")
    logging.info(f"Log file: {log_file}")
    logging.info("All stage logs will be captured in this single file")
    logging.info("=" * 80)
    
    return log_file

def run_initial_test_generation(config: PipelineConfig):
    """Run initial test suite generation using LLMs."""
    logging.info("=" * 80)
    logging.info("STAGE 1: INITIAL TEST GENERATION USING LLMs")
    logging.info("=" * 80)
    logging.info(f"Module: {config.module_name}")
    logging.info(f"Target functions: {config.function_names}")
    logging.info(f"Source directory: {config.source_dir}")
    logging.info(f"Tests directory: {config.tests_dir}")
    
    try:
        logging.info("Initializing TestGenerationPipeline...")
        pipeline = TestGenerationPipeline(config)
        
        logging.info("Starting LLM test generation process...")
        test_files = pipeline.generate_test_suite()
        
        logging.info("=" * 40)
        logging.info("LLM TEST GENERATION RESULTS")
        logging.info("=" * 40)
        logging.info(f"Number of test files generated: {len(test_files)}")
        for i, test_file in enumerate(test_files, 1):
            logging.info(f"  {i}. {test_file}")
            
            # Log basic info about each test file
            try:
                test_path = Path(test_file)
                if test_path.exists():
                    file_size = test_path.stat().st_size
                    with open(test_path, 'r') as f:
                        line_count = len(f.readlines())
                    logging.info(f"     Size: {file_size} bytes, Lines: {line_count}")
                else:
                    logging.warning(f"     File does not exist: {test_path}")
            except Exception as e:
                logging.warning(f"     Could not read file stats: {e}")
        
        logging.info("=" * 40)
        logging.info("STAGE 1 COMPLETED SUCCESSFULLY")
        logging.info("=" * 40)
        
        return test_files
    except Exception as e:
        logging.error("=" * 40)
        logging.error("STAGE 1 FAILED")
        logging.error("=" * 40)
        logging.error(f"Error during initial test generation: {e}")
        import traceback
        logging.error("Full traceback:")
        for line in traceback.format_exc().splitlines():
            logging.error(f"  {line}")
        logging.error("=" * 40)
        return []

def run_normalization(config: PipelineConfig):
    """Run test normalization to create Pynguin seeds."""
    logging.info("=" * 80)
    logging.info("STAGE 2: TEST NORMALIZATION FOR PYNGUIN COMPATIBILITY")
    logging.info("=" * 80)
    logging.info(f"Module: {config.module_name}")
    logging.info(f"Functions to normalize: {config.function_names}")
    logging.info(f"Source tests directory: {config.tests_dir}")
    
    try:
        logging.info("Creating normalization configuration...")
        # Create normalization config
        norm_config = ExtractionConfig(
            module_name=config.module_name,
            function_names=config.function_names,
            tests_dir=config.tests_dir
        )
        
        logging.info("Normalization config created:")
        logging.info(f"  - Module: {norm_config.module_name}")
        logging.info(f"  - Functions: {norm_config.function_names}")
        logging.info(f"  - Tests dir: {norm_config.tests_dir}")
        
        logging.info("Starting seed file generation...")
        # Generate seed file
        seed_file = generate_seed_file(norm_config)
        
        if seed_file:
            logging.info("=" * 40)
            logging.info("NORMALIZATION RESULTS")
            logging.info("=" * 40)
            logging.info(f"Seed file generated: {seed_file}")
            
            # Log seed file details
            try:
                seed_path = Path(seed_file)
                if seed_path.exists():
                    file_size = seed_path.stat().st_size
                    with open(seed_path, 'r') as f:
                        content = f.read()
                        line_count = len(content.splitlines())
                    logging.info(f"Seed file size: {file_size} bytes")
                    logging.info(f"Seed file lines: {line_count}")
                    logging.info("Seed file preview (first 10 lines):")
                    for i, line in enumerate(content.splitlines()[:10], 1):
                        logging.info(f"  {i:2d}: {line}")
                    if line_count > 10:
                        logging.info(f"  ... ({line_count - 10} more lines)")
                else:
                    logging.warning(f"Seed file does not exist: {seed_path}")
            except Exception as e:
                logging.warning(f"Could not read seed file details: {e}")
            
            logging.info("=" * 40)
            logging.info("STAGE 2 COMPLETED SUCCESSFULLY")
            logging.info("=" * 40)
        else:
            logging.error("Seed file generation returned None")
        
        return seed_file
    except Exception as e:
        logging.error("=" * 40)
        logging.error("STAGE 2 FAILED")
        logging.error("=" * 40)
        logging.error(f"Error during normalization: {e}")
        import traceback
        logging.error("Full traceback:")
        for line in traceback.format_exc().splitlines():
            logging.error(f"  {line}")
        logging.error("=" * 40)
        return None

def run_evolutionary_algorithm(config: PipelineConfig, seed_file: str):
    """Run evolutionary algorithm using Pynguin with dynamic population."""
    logging.info("=" * 80)
    logging.info("STAGE 3: EVOLUTIONARY ALGORITHM (POPULATION MANAGEMENT + PYNGUIN)")
    logging.info("=" * 80)
    logging.info(f"Module: {config.module_name}")
    logging.info(f"Seed file: {seed_file}")
    
    try:
        logging.info("Importing evolutionary algorithm components...")
        # Import EA components
        from evolutionary_algo_integration.simple_population_manager import auto_adjust_population_for_module
        
        logging.info("Calculating optimal population size...")
        # Adjust population size based on module complexity
        population_size = auto_adjust_population_for_module(config.module_name)
        
        logging.info("=" * 40)
        logging.info("POPULATION OPTIMIZATION RESULTS")
        logging.info("=" * 40)
        logging.info(f"Optimal population size: {population_size}")
        logging.info("=" * 40)
        
        logging.info("Starting Pynguin execution with optimized population...")
        # Run Pynguin with the optimized population size
        pynguin_result = run_pynguin(config, seed_file, population_size)
        
        if pynguin_result and pynguin_result['success']:
            logging.info("=" * 40)
            logging.info("EVOLUTIONARY ALGORITHM COMPLETED SUCCESSFULLY")
            logging.info("=" * 40)
            logging.info(f"Population size used: {population_size}")
            logging.info(f"Pynguin file: {pynguin_result.get('output_file')}")
            logging.info(f"Status: Completed")
            logging.info(f"Method: Full Pynguin execution")
            logging.info("=" * 40)
            logging.info("STAGE 3 COMPLETED SUCCESSFULLY")
            logging.info("=" * 40)
            
            return {
                'population_size': population_size,
                'status': 'completed',
                'method': 'pynguin_execution',
                'pynguin_file': pynguin_result.get('output_file')
            }
        else:
            logging.warning("=" * 40)
            logging.warning("EVOLUTIONARY ALGORITHM PARTIALLY SUCCESSFUL")
            logging.warning("=" * 40)
            logging.warning("Pynguin execution failed, but population adjustment succeeded")
            logging.warning(f"Population size calculated: {population_size}")
            logging.warning("Status: Partial (population optimization only)")
            logging.warning("=" * 40)
            logging.warning("STAGE 3 COMPLETED WITH WARNINGS")
            logging.warning("=" * 40)
            
            return {
                'population_size': population_size,
                'status': 'partial',
                'method': 'population_adjustment_only'
            }
            
    except Exception as e:
        logging.error("=" * 40)
        logging.error("STAGE 3 FAILED - EVOLUTIONARY ALGORITHM ERROR")
        logging.error("=" * 40)
        logging.error(f"Error during evolutionary algorithm: {e}")
        import traceback
        logging.error("Full traceback:")
        for line in traceback.format_exc().splitlines():
            logging.error(f"  {line}")
        logging.error("=" * 40)
        return None


def switch_to_environment(env_name: str):
    """Switch to a specific Python environment."""
    if env_name == "myvenv":
        python_path = Path(__file__).parent / "myvenv" / "bin" / "python3"
    elif env_name == "my_pynguin_venv":
        python_path = Path(__file__).parent / "pynguin-main" / "my_pynguin_venv" / "bin" / "python3"
    else:
        raise ValueError(f"Unknown environment: {env_name}")
    
    if not python_path.exists():
        raise FileNotFoundError(f"Python environment not found: {python_path}")
    
    return str(python_path)

def log_subprocess_output(stage_name: str, process_result, log_stdout=True, log_stderr=True):
    """Log subprocess output with proper stage identification."""
    logging.info("=" * 60)
    logging.info(f"{stage_name.upper()} - SUBPROCESS OUTPUT")
    logging.info("=" * 60)
    
    if hasattr(process_result, 'returncode'):
        logging.info(f"Return Code: {process_result.returncode}")
    
    if log_stdout and hasattr(process_result, 'stdout') and process_result.stdout:
        logging.info("STDOUT:")
        logging.info("-" * 40)
        for line in process_result.stdout.splitlines():
            logging.info(f"STDOUT: {line}")
        logging.info("-" * 40)
    
    if log_stderr and hasattr(process_result, 'stderr') and process_result.stderr:
        logging.info("STDERR:")
        logging.info("-" * 40)
        for line in process_result.stderr.splitlines():
            logging.warning(f"STDERR: {line}")
        logging.info("-" * 40)
    
    logging.info("=" * 60)

def run_subprocess_with_comprehensive_logging(cmd: list, stage_name: str, **kwargs):
    """Run subprocess with comprehensive logging of all output."""
    logging.info("=" * 60)
    logging.info(f"{stage_name.upper()} - COMMAND EXECUTION")
    logging.info("=" * 60)
    logging.info(f"Command: {' '.join(cmd)}")
    logging.info(f"Working Directory: {kwargs.get('cwd', 'current')}")
    
    # Ensure we capture output
    kwargs.setdefault('capture_output', True)
    kwargs.setdefault('text', True)
    
    try:
        result = subprocess.run(cmd, **kwargs)
        log_subprocess_output(stage_name, result)
        return result
    except subprocess.TimeoutExpired as e:
        logging.error(f"{stage_name} - TIMEOUT: {e}")
        if hasattr(e, 'stdout') and e.stdout:
            logging.info("Partial STDOUT before timeout:")
            for line in e.stdout.splitlines():
                logging.info(f"STDOUT: {line}")
        raise
    except Exception as e:
        logging.error(f"{stage_name} - ERROR: {e}")
        raise
def run_subprocess_with_env(cmd: list, env_name: str, cwd: str = None, stage_name: str = "SUBPROCESS", **kwargs):
    """Run a subprocess with a specific Python environment and comprehensive logging."""
    python_path = switch_to_environment(env_name)
    
    # Replace 'python' or 'python3' with the specific environment python
    if cmd[0] in ['python', 'python3', sys.executable]:
        cmd[0] = python_path
    
    logging.info("=" * 60)
    logging.info(f"{stage_name.upper()} - ENVIRONMENT EXECUTION")
    logging.info("=" * 60)
    logging.info(f"Environment: {env_name} ({python_path})")
    logging.info(f"Command: {' '.join(cmd)}")
    logging.info(f"Working Directory: {cwd or 'current'}")
    
    # Set up environment variables with cache disabling
    env = os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['PYTHONPYCACHEPREFIX'] = '/tmp/disabled_pycache'
    env['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
    
    # Ensure we capture output for logging
    kwargs.setdefault('capture_output', True)
    kwargs.setdefault('text', True)
    
    try:
        if cwd:
            result = subprocess.run(cmd, cwd=cwd, env=env, **kwargs)
        else:
            result = subprocess.run(cmd, env=env, **kwargs)
        
        log_subprocess_output(stage_name, result)
        return result
    except Exception as e:
        logging.error(f"{stage_name} - EXECUTION ERROR: {e}")
        raise

def run_pynguin(config: PipelineConfig, seed_file: str, population_size: int):
    """Execute Pynguin to generate evolutionary test suite using my_pynguin_venv."""
    logging.info("=" * 80)
    logging.info("STAGE 3: PYNGUIN EVOLUTIONARY TEST GENERATION")
    logging.info("=" * 80)
    logging.info(f"Module: {config.module_name}")
    logging.info(f"Population size: {population_size}")
    logging.info(f"Seed file: {seed_file}")
    
    try:
        # Prepare Pynguin command with my_pynguin_venv
        # Use absolute paths to avoid confusion with Pynguin's working directory
        workspace_root = Path(__file__).parent
        source_file = workspace_root / config.source_dir / f"{config.module_name}.py"
        output_dir = workspace_root / config.tests_dir / "pynguin_tests"
        output_dir.mkdir(exist_ok=True)
        
        # Project path should be the workspace root (where tests/ directory is located)
        project_path = workspace_root
        
        pynguin_path = workspace_root / "pynguin-main"
        pynguin_python = pynguin_path / "my_pynguin_venv" / "bin" / "python3"
        
        logging.info("Pynguin environment verification:")
        logging.info(f"  - Workspace root: {workspace_root}")
        logging.info(f"  - Source file: {source_file}")
        logging.info(f"  - Output directory: {output_dir}")
        logging.info(f"  - Project path: {project_path}")
        logging.info(f"  - Pynguin path: {pynguin_path}")
        logging.info(f"  - Python executable: {pynguin_python}")
        
        # Verify Pynguin environment exists
        if not pynguin_python.exists():
            raise FileNotFoundError(f"Pynguin Python environment not found: {pynguin_python}")
        
        logging.info("✓ Pynguin environment verified")
        
        cmd = [
            str(pynguin_python), "-m", "pynguin",
            "--project-path", str(project_path.resolve()),  # Force absolute path resolution
            "--output-path", str(output_dir.resolve()),     # Force absolute path resolution  
            "--module-name", config.module_name,
            "--maximum-search-time", "180",  # 3 minutes for testing
            "--population", str(population_size),
            "--initial_population_data", str((workspace_root / config.tests_dir).resolve()),  # Force absolute path resolution
            "--verbose"  # Add verbose logging
        ]
        
        logging.info("Pynguin command configuration:")
        logging.info(f"Command: {' '.join(cmd)}")
        logging.info(f"Working directory: {pynguin_path}")
        
        # Set PYTHONPATH to include pynguin
        env = os.environ.copy()
        env["PYTHONPATH"] = str(pynguin_path / "src") + ":" + env.get("PYTHONPATH", "")
        env["PYNGUIN_DANGER_AWARE"] = "1"  # Enable Pynguin execution
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        env['PYTHONPYCACHEPREFIX'] = '/tmp/disabled_pycache'
        
        logging.info("Environment variables:")
        logging.info(f"  - PYTHONPATH: {env['PYTHONPATH']}")
        logging.info(f"  - PYNGUIN_DANGER_AWARE: {env['PYNGUIN_DANGER_AWARE']}")
        
        # Run Pynguin with real-time output
        logging.info("Starting Pynguin execution...")
        process = subprocess.Popen(
            cmd,
            cwd=str(pynguin_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
            bufsize=1,
            universal_newlines=True
        )
        
        # Stream output in real-time
        output_lines = []
        logging.info("=" * 60)
        logging.info("PYNGUIN EXECUTION LOG (REAL-TIME)")
        logging.info("=" * 60)
        
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                line = output.strip()
                output_lines.append(line)
                logging.info(f"PYNGUIN: {line}")
        
        # Wait for process to complete
        return_code = process.poll()
        full_output = '\n'.join(output_lines)
        
        logging.info("=" * 60)
        logging.info("PYNGUIN EXECUTION COMPLETED")
        logging.info("=" * 60)
        logging.info(f"Return code: {return_code}")
        logging.info(f"Total output lines: {len(output_lines)}")
        
        if return_code == 0:
            # Look for generated test file with absolute path
            generated_file = output_dir / f"pynguin_generated_test_{config.module_name}.py"
            
            logging.info("Checking for generated files...")
            logging.info(f"Expected file: {generated_file}")
            
            if generated_file.exists():
                # Log details about generated file
                file_size = generated_file.stat().st_size
                with open(generated_file, 'r') as f:
                    content = f.read()
                    line_count = len(content.splitlines())
                
                logging.info("=" * 40)
                logging.info("PYNGUIN GENERATION SUCCESSFUL")
                logging.info("=" * 40)
                logging.info(f"Generated file: {generated_file}")
                logging.info(f"File size: {file_size} bytes")
                logging.info(f"Line count: {line_count}")
                logging.info("File preview (first 15 lines):")
                for i, line in enumerate(content.splitlines()[:15], 1):
                    logging.info(f"  {i:2d}: {line}")
                if line_count > 15:
                    logging.info(f"  ... ({line_count - 15} more lines)")
                logging.info("=" * 40)
                logging.info("STAGE 3 COMPLETED SUCCESSFULLY")
                logging.info("=" * 40)
                
                return {
                    'success': True,
                    'output_file': str(generated_file),
                    'stdout': full_output,
                    'stderr': ''
                }
            else:
                logging.warning("Pynguin completed but no test file found")
                # Debug: check what files were actually created
                if output_dir.exists():
                    actual_files = list(output_dir.glob("*.py"))
                    logging.info(f"Files found in output directory: {actual_files}")
                    for file in actual_files:
                        logging.info(f"  - {file} ({file.stat().st_size} bytes)")
                
                logging.error("=" * 40)
                logging.error("STAGE 3 FAILED - NO OUTPUT FILE")
                logging.error("=" * 40)
                return {
                    'success': False,
                    'error': 'No output file generated',
                    'stdout': full_output,
                    'stderr': ''
                }
        else:
            logging.error("=" * 40)
            logging.error("STAGE 3 FAILED - PYNGUIN ERROR")
            logging.error("=" * 40)
            logging.error(f"Pynguin failed with return code {return_code}")
            return {
                'success': False,
                'error': f"Pynguin failed with code {return_code}",
                'stdout': full_output,
                'stderr': ''
            }
            
    except subprocess.TimeoutExpired:
        logging.error("=" * 40)
        logging.error("STAGE 3 FAILED - TIMEOUT")
        logging.error("=" * 40)
        logging.error("Pynguin execution timed out")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logging.error("=" * 40)
        logging.error("STAGE 3 FAILED - EXCEPTION")
        logging.error("=" * 40)
        logging.error(f"Error during Pynguin execution: {e}")
        import traceback
        logging.error("Full traceback:")
        for line in traceback.format_exc().splitlines():
            logging.error(f"  {line}")
        logging.error("=" * 40)
        return {'success': False, 'error': str(e)}


def run_test_merging(config: PipelineConfig):
    """Merge LLM and Pynguin test suites using myvenv environment."""
    logging.info("=" * 80)
    logging.info("STAGE 4: TEST SUITE MERGING (LLM + PYNGUIN)")
    logging.info("=" * 80)
    logging.info(f"Module: {config.module_name}")
    
    try:
        # Run the merger script using myvenv with the correct module name
        merger_script = Path(__file__).parent / "evolutionary_algo_integration" / "llm_ea_tests" / "run_merger.py"
        python_path = switch_to_environment("myvenv")
        
        logging.info("Test merging configuration:")
        logging.info(f"  - Merger script: {merger_script}")
        logging.info(f"  - Python environment: {python_path}")
        logging.info(f"  - Module: {config.module_name}")
        
        cmd = [python_path, str(merger_script), config.module_name]
        
        logging.info("Starting test merger execution...")
        result = run_subprocess_with_comprehensive_logging(
            cmd, 
            "TEST_MERGING",
            cwd=str(Path(__file__).parent),
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            # The merger script saves to the standard location
            merged_file = Path(config.tests_dir) / f"llm_generated_test_{config.module_name}.py"
            
            logging.info("Verifying merged file...")
            logging.info(f"Expected merged file: {merged_file}")
            
            if merged_file.exists():
                # Log details about merged file
                file_size = merged_file.stat().st_size
                with open(merged_file, 'r') as f:
                    content = f.read()
                    line_count = len(content.splitlines())
                
                logging.info("=" * 40)
                logging.info("TEST MERGING SUCCESSFUL")
                logging.info("=" * 40)
                logging.info(f"Merged file: {merged_file}")
                logging.info(f"File size: {file_size} bytes")
                logging.info(f"Line count: {line_count}")
                logging.info("Merged file preview (first 20 lines):")
                for i, line in enumerate(content.splitlines()[:20], 1):
                    logging.info(f"  {i:2d}: {line}")
                if line_count > 20:
                    logging.info(f"  ... ({line_count - 20} more lines)")
                logging.info("=" * 40)
                logging.info("STAGE 4 COMPLETED SUCCESSFULLY")
                logging.info("=" * 40)
                
                return {'success': True, 'merged_file': str(merged_file)}
            else:
                logging.error("Merge script completed but merged file not found")
                
                # Debug: Check what files exist in tests directory
                tests_dir = Path(config.tests_dir)
                if tests_dir.exists():
                    existing_files = list(tests_dir.glob("*.py"))
                    logging.info("Files found in tests directory:")
                    for file in existing_files:
                        logging.info(f"  - {file}")
                
                logging.error("=" * 40)
                logging.error("STAGE 4 FAILED - MERGED FILE NOT FOUND")
                logging.error("=" * 40)
                return {'success': False, 'error': 'Merged file not found'}
        else:
            logging.error("=" * 40)
            logging.error("STAGE 4 FAILED - MERGE SCRIPT ERROR")
            logging.error("=" * 40)
            logging.error(f"Test merging failed with return code {result.returncode}")
            return {'success': False, 'error': f'Merge script failed with code {result.returncode}'}
            
    except Exception as e:
        logging.error("=" * 40)
        logging.error("STAGE 4 FAILED - EXCEPTION")
        logging.error("=" * 40)
        logging.error(f"Error during test merging: {e}")
        import traceback
        logging.error("Full traceback:")
        for line in traceback.format_exc().splitlines():
            logging.error(f"  {line}")
        logging.error("=" * 40)
        return {'success': False, 'error': str(e)}


def run_test_repair(merged_file: str, config: PipelineConfig):
    """Run automated test repair on the merged test suite."""
    logging.info("=" * 80)
    logging.info("STAGE 5: AUTOMATED TEST REPAIR")
    logging.info("=" * 80)
    logging.info(f"Module: {config.module_name}")
    logging.info(f"Merged file: {merged_file}")
    
    try:
        logging.info("Initializing TestSuiteManager...")
        test_manager = TestSuiteManager()
        source_dir = config.source_dir
        
        logging.info("Test repair configuration:")
        logging.info(f"  - Test file: {merged_file}")
        logging.info(f"  - Source directory: {source_dir}")
        logging.info(f"  - Max repair attempts: {MAX_REPAIR_ATTEMPTS}")
        
        # Run tests with repair
        logging.info("Starting test execution with repair mechanism...")
        repair_results = run_tests_with_repair(
            test_manager, 
            merged_file, 
            config.module_name,
            source_dir
        )
        
        if repair_results['success']:
            logging.info("=" * 40)
            logging.info("TEST REPAIR SUCCESSFUL")
            logging.info("=" * 40)
            logging.info("All tests are working correctly after repair!")
            logging.info(f"Final test file: {merged_file}")
            
            # Log repair results details
            if 'output' in repair_results:
                logging.info("Test execution output:")
                for line in repair_results['output'].splitlines():
                    logging.info(f"  TEST: {line}")
            
            logging.info("=" * 40)
            logging.info("STAGE 5 COMPLETED SUCCESSFULLY")
            logging.info("=" * 40)
            
            return {'success': True, 'final_file': merged_file, 'results': repair_results}
        else:
            logging.warning("=" * 40)
            logging.warning("TEST REPAIR FAILED")
            logging.warning("=" * 40)
            logging.warning(f"Tests failed after {MAX_REPAIR_ATTEMPTS} repair attempts")
            logging.warning(f"Final test file: {merged_file}")
            
            # Log failure details
            if 'output' in repair_results:
                logging.warning("Final test execution output:")
                for line in repair_results['output'].splitlines():
                    logging.warning(f"  TEST: {line}")
            
            logging.warning("=" * 40)
            logging.warning("STAGE 5 COMPLETED WITH WARNINGS")
            logging.warning("=" * 40)
            
            return {'success': False, 'final_file': merged_file, 'results': repair_results}
            
    except Exception as e:
        logging.error("=" * 40)
        logging.error("STAGE 5 FAILED - TEST REPAIR ERROR")
        logging.error("=" * 40)
        logging.error(f"Error during test repair: {e}")
        import traceback
        logging.error("Full traceback:")
        for line in traceback.format_exc().splitlines():
            logging.error(f"  {line}")
        logging.error("=" * 40)
        return {'success': False, 'error': str(e)}


def run_tests_with_repair(test_manager, test_file_path, source_filename, source_dir):
    """Run tests with automatic repair mechanism."""
    attempt = 0
    
    logging.info("=" * 50)
    logging.info("TEST REPAIR MECHANISM")
    logging.info("=" * 50)
    logging.info(f"Auto-repair enabled with max {MAX_REPAIR_ATTEMPTS} attempts")
    logging.info(f"Test file: {test_file_path}")
    logging.info(f"Source file: {source_filename}")
    logging.info(f"Source directory: {source_dir}")
    logging.info("=" * 50)
    
    while attempt <= MAX_REPAIR_ATTEMPTS:
        logging.info("-" * 40)
        if attempt > 0:
            logging.info(f"REPAIR ATTEMPT {attempt}/{MAX_REPAIR_ATTEMPTS}")
        else:
            logging.info("INITIAL TEST EXECUTION")
        logging.info("-" * 40)
        
        # Run tests on current test file
        logging.info("Running tests...")
        results = test_manager.run_tests(test_file_path, source_dir)
        
        # Log test results
        logging.info(f"Test execution result: {'SUCCESS' if results['success'] else 'FAILED'}")
        if 'output' in results and results['output']:
            logging.info("Test output:")
            for line in results['output'].splitlines()[:20]:  # Limit to first 20 lines
                logging.info(f"  TEST: {line}")
            if len(results['output'].splitlines()) > 20:
                logging.info("  ... (output truncated)")
        
        if results['success']:
            logging.info(f"Tests passed on attempt {attempt + 1}!")
            logging.info("=" * 50)
            logging.info("TEST REPAIR COMPLETED SUCCESSFULLY")
            logging.info("=" * 50)
            return results
        
        if attempt >= MAX_REPAIR_ATTEMPTS:
            logging.warning(f"Test repair failed after {MAX_REPAIR_ATTEMPTS} attempts")
            logging.warning("=" * 50)
            logging.warning("TEST REPAIR EXHAUSTED ALL ATTEMPTS")
            logging.warning("=" * 50)
            return results
        
        logging.info(f"Tests failed on attempt {attempt + 1}, attempting repair...")
        
        # Get repaired code from LLM (sending only error output, no source file)
        logging.info("Requesting LLM repair...")
        repaired_code = test_manager.repair_test_with_llm(results['output'], source_filename)
        
        if repaired_code:
            # Overwrite the test file with repaired code
            try:
                logging.info("Applying repaired code...")
                cleaned_repaired_code = test_manager._clean_test_code(repaired_code)
                
                # Log a preview of the repaired code
                logging.info("Repaired code preview (first 10 lines):")
                for i, line in enumerate(cleaned_repaired_code.splitlines()[:10], 1):
                    logging.info(f"  {i:2d}: {line}")
                
                with open(test_file_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned_repaired_code)
                
                logging.info(f"Test file overwritten with repaired code: {test_file_path}")
                attempt += 1
            except Exception as e:
                logging.error(f"Failed to overwrite test file: {e}")
                return results
        else:
            logging.warning("Could not get repaired code from LLM, stopping")
            return results
            
    return results

def main():
    """Main pipeline execution with environment switching."""
    if len(sys.argv) != 2:
        print("Usage: python main_pipeline.py <module_name>")
        print("Example: python main_pipeline.py sample_calculator")
        sys.exit(1)
    
    module_name = sys.argv[1]
    
    # Setup comprehensive logging for entire pipeline
    log_file = setup_logging(module_name)
    logging.info(f"Starting complete pipeline for {module_name}")
    logging.info(f"Complete audit log file: {log_file}")
    
    # Clean up cache directories at the start
    logging.info("Performing initial cache cleanup...")
    cleanup_cache_directories()
    
    # Verify environments exist
    try:
        myvenv_python = switch_to_environment("myvenv")
        pynguin_python = switch_to_environment("my_pynguin_venv")
        logging.info(f"Main environment (myvenv): {myvenv_python}")
        logging.info(f"Pynguin environment (my_pynguin_venv): {pynguin_python}")
    except Exception as e:
        logging.error(f"Environment verification failed: {e}")
        sys.exit(1)
    
    try:
        # Create pipeline configuration
        # Create dynamic configuration that automatically extracts function names
        logging.info("Analyzing source file for function extraction...")
        config = create_dynamic_pipeline_config(module_name)
        logging.info(f"Final Configuration: {config}")
        
        # Step 1: Initial test generation (using myvenv)
        logging.info("=" * 60)
        logging.info("STEP 1: INITIAL TEST GENERATION (myvenv)")
        logging.info("=" * 60)
        
        # Run LLM generation (re-enabled after testing dynamic system)
        test_files = run_initial_test_generation(config)
        
        if not test_files:
            logging.warning("No test files generated by LLM. Checking for existing files...")
            # Check if there's an existing test file
            existing_test = Path(config.tests_dir) / f"llm_generated_test_{module_name}.py"
            if existing_test.exists():
                test_files = [str(existing_test)]
                logging.info(f"Using existing test file: {existing_test}")
            else:
                logging.error("No test files available. Exiting.")
                sys.exit(1)
        
        # Step 2: Normalization (using myvenv)
        logging.info("=" * 60)
        logging.info("STEP 2: TEST NORMALIZATION (myvenv)")
        logging.info("=" * 60)
        seed_file = run_normalization(config)
        if not seed_file:
            logging.error("Failed to generate seed file. Exiting.")
            sys.exit(1)
        
        # Step 3: Evolutionary algorithm (using my_pynguin_venv)
        logging.info("=" * 60)
        logging.info("STEP 3: EVOLUTIONARY ALGORITHM (my_pynguin_venv)")
        logging.info("=" * 60)
        ea_results = run_evolutionary_algorithm(config, seed_file)
        
        # Step 4: Test merging (LLM + Pynguin) (using myvenv)
        pynguin_available = ea_results and ea_results.get('pynguin_file')
        if pynguin_available:
            logging.info("=" * 60)
            logging.info("STEP 4: TEST SUITE MERGING (myvenv)")
            logging.info("=" * 60)
            merge_results = run_test_merging(config)
            
            if merge_results['success']:
                # Step 5: Test repair (using myvenv)
                logging.info("=" * 60)
                logging.info("STEP 5: AUTOMATED TEST REPAIR (myvenv)")
                logging.info("=" * 60)
                repair_results = run_test_repair(merge_results['merged_file'], config)
                
                # Step 6: Complete Mutation Testing Pipeline (using mutpy_env)
                logging.info("=" * 60)
                logging.info("STEP 6: COMPLETE MUTATION TESTING PIPELINE (mutpy_env)")
                logging.info("=" * 60)
                mutation_results = run_mutation_testing_pipeline(config)
                
                # Final summary
                logging.info("=" * 80)
                logging.info("COMPLETE PIPELINE EXECUTION SUCCESSFUL! 🎉")
                logging.info("=" * 80)
                logging.info("COMPREHENSIVE PIPELINE SUMMARY:")
                logging.info(f"  Module processed: {config.module_name}")
                logging.info(f"  Generated test files: {len(test_files)}")
                logging.info(f"  Seed file created: {seed_file}")
                if ea_results:
                    logging.info(f"  Population size optimized: {ea_results.get('population_size', 'N/A')}")
                    logging.info(f"  Pynguin file generated: {ea_results.get('pynguin_file', 'N/A')}")
                logging.info(f"  Test suites merged: {merge_results['merged_file']}")
                if repair_results['success']:
                    logging.info("  Test repair: All tests passing")
                else:
                    logging.info("  Test repair: Some tests still failing")
                
                # Comprehensive mutation testing results
                if mutation_results['success']:
                    logging.info("  Mutation testing: Completed successfully")
                    logging.info(f"    • Initial Score: {mutation_results.get('initial_mutation_score', 'N/A')}")
                    logging.info(f"    • Final Score: {mutation_results.get('final_mutation_score', 'N/A')}")
                    logging.info(f"    • Surviving Mutants: {mutation_results.get('surviving_mutants', 'N/A')}")
                    if mutation_results.get('killer_tests_generated'):
                        logging.info("    • Killer Tests: Generated and integrated ✓")
                    if mutation_results.get('perfect_score_achieved'):
                        logging.info("    • PERFECT SCORE: 100% mutation coverage achieved!")
                    logging.info(f"    • Results CSV: {mutation_results.get('results_csv', 'N/A')}")
                    logging.info(f"    • Test Suite Used: {mutation_results.get('merged_test_file', 'N/A')}")
                else:
                    logging.info(f"  Mutation testing: Failed - {mutation_results.get('error', 'Unknown error')}")
                
                logging.info("=" * 80)
                logging.info("PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
                logging.info("=" * 80)
            else:
                logging.error("Test merging failed, but individual components succeeded")
        else:
            logging.warning("Pynguin execution failed. Only LLM tests and population adjustment available.")
            
            # Still run complete mutation testing on LLM tests only
            logging.info("=" * 60)
            logging.info("STEP 4: COMPLETE MUTATION TESTING PIPELINE (mutpy_env) - LLM Tests Only")
            logging.info("=" * 60)
            mutation_results = run_mutation_testing_pipeline(config)
            
            # Final summary without merging
            logging.info("=" * 80)
            logging.info("PIPELINE COMPLETED (PARTIAL EXECUTION) ⚠️")
            logging.info("=" * 80)
            logging.info("PARTIAL PIPELINE SUMMARY:")
            logging.info(f"  Module processed: {config.module_name}")
            logging.info(f"  Generated test files: {len(test_files)}")
            logging.info(f"  Seed file created: {seed_file}")
            if ea_results:
                logging.info(f"  Population size optimized: {ea_results.get('population_size', 'N/A')}")
            logging.info("  Test merging: Skipped (Pynguin execution failed)")
            logging.info("  Note: Using LLM-generated tests only for mutation testing")
            
            # Comprehensive mutation testing results for LLM-only
            if mutation_results['success']:
                logging.info("  Mutation testing (LLM only): Completed successfully")
                logging.info(f"    • Initial Score: {mutation_results.get('initial_mutation_score', 'N/A')}")
                logging.info(f"    • Final Score: {mutation_results.get('final_mutation_score', 'N/A')}")
                logging.info(f"    • Surviving Mutants: {mutation_results.get('surviving_mutants', 'N/A')}")
                if mutation_results.get('killer_tests_generated'):
                    logging.info("    • Killer Tests: Generated and integrated ✓")
                if mutation_results.get('perfect_score_achieved'):
                    logging.info("    • PERFECT SCORE: 100% mutation coverage achieved!")
                logging.info(f"    • Results CSV: {mutation_results.get('results_csv', 'N/A')}")
                logging.info(f"    • Test Suite Used: {mutation_results.get('merged_test_file', 'N/A')}")
            else:
                logging.info(f"  Mutation testing: Failed - {mutation_results.get('error', 'Unknown error')}")
            
            logging.info("=" * 80)
            logging.info("PIPELINE EXECUTION COMPLETED (PARTIAL)")
            logging.info("=" * 80)
        
        # Final cache cleanup
        logging.info("Performing final cache cleanup...")
        cleanup_cache_directories()
        
    except Exception as e:
        logging.error(f"Pipeline failed: {e}")
        import traceback
        logging.error(traceback.format_exc())
        
        # Cache cleanup even on failure
        logging.info("Performing cache cleanup after failure...")
        cleanup_cache_directories()
        
        logging.info("=" * 60)
        logging.info("TROUBLESHOOTING INFORMATION")
        logging.info("=" * 60)
        logging.info("Environment Requirements:")
        logging.info("  - myvenv: Python 3.13+ with LLM dependencies (phases 1, 3)")
        logging.info("  - my_pynguin_venv: Python 3.10 with Pynguin (phase 2)")
        logging.info("Make sure both environments are properly set up.")
        sys.exit(1)

if __name__ == "__main__":
    main()
