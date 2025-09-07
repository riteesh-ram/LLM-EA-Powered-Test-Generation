#!/usr/bin/env python3
"""
Standalone Pynguin test generation script.
This bypasses all LLM generation, normalization complexity and     # Build Pynguin command with corrected argument names
    cmd = [
        str(pynguin_python), "-m", "pynguin",
        "--project-path", str(workspace_root.resolve()),
        "--output-path", str(output_dir.resolve()),
        "--module-name", module_name,
        "--maximum-search-time", "60",
        "--population", str(min(population_size, 50)),
        "--initial-population-seeding", "True",
        "--initial-population-data", str(Path(seed_file).parent.resolve()),
        "--seeded-testcases-reuse-probability", "0.8",
        "--initial-population-mutations", "3",
        "--maximum-test-execution-timeout", "3",
        "--maximum-memory", "1500",
        "--verbose"
    ]ectly.
"""

import sys
import os
import subprocess
import logging
from pathlib import Path
from datetime import datetime

def setup_simple_logging(module_name: str):
    """Setup simple logging for Pynguin execution."""
    log_dir = Path(__file__).parent / "pipeline_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"pynguin_only_{module_name}_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, mode='w', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ],
        force=True
    )
    
    logging.info("=" * 60)
    logging.info("PYNGUIN-ONLY TEST GENERATION STARTED")
    logging.info("=" * 60)
    logging.info(f"Module: {module_name}")
    logging.info(f"Log file: {log_file}")
    
    return log_file

def check_prerequisites(module_name: str):
    """Check if all required files exist."""
    workspace_root = Path(__file__).parent
    
    # Check source file
    source_file = workspace_root / "tests" / "source" / f"{module_name}.py"
    if not source_file.exists():
        logging.error(f"Source file not found: {source_file}")
        return False
    
    # Check seed file
    seed_file = workspace_root / "tests" / "test_suites" / f"test_{module_name}_seed.py"
    if not seed_file.exists():
        logging.error(f"Seed file not found: {seed_file}")
        return False
    
    # Check Pynguin environment
    pynguin_python = workspace_root / "pynguin-main" / "my_pynguin_venv" / "bin" / "python3"
    if not pynguin_python.exists():
        logging.error(f"Pynguin environment not found: {pynguin_python}")
        return False
    
    logging.info("All prerequisites found:")
    logging.info(f"  - Source file: {source_file}")
    logging.info(f"  - Seed file: {seed_file}")
    logging.info(f"  - Pynguin env: {pynguin_python}")
    
    return True

def calculate_dynamic_population(module_name: str):
    """Calculate population size based on source code complexity."""
    try:
        workspace_root = Path(__file__).parent
        source_file = workspace_root / "tests" / "source" / f"{module_name}.py"
        
        # Read source file and analyze complexity
        with open(source_file, 'r') as f:
            content = f.read()
        
        lines = content.splitlines()
        function_count = len([line for line in lines if line.strip().startswith('def ')])
        class_count = len([line for line in lines if line.strip().startswith('class ')])
        loc = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
        
        # Calculate dynamic population based on complexity
        base_population = 50
        function_factor = function_count * 15
        class_factor = class_count * 25
        loc_factor = min(loc // 10, 50)  # Cap LOC contribution
        
        dynamic_population = base_population + function_factor + class_factor + loc_factor
        
        # Ensure reasonable bounds for population size
        dynamic_population = max(30, min(dynamic_population, 200))  # Allow larger population
        
        logging.info("=" * 40)
        logging.info("DYNAMIC POPULATION CALCULATION")
        logging.info("=" * 40)
        logging.info(f"Functions detected: {function_count}")
        logging.info(f"Classes detected: {class_count}")
        logging.info(f"Lines of code: {loc}")
        logging.info(f"Base population: {base_population}")
        logging.info(f"Function contribution: {function_factor}")
        logging.info(f"Class contribution: {class_factor}")
        logging.info(f"LOC contribution: {loc_factor}")
        logging.info(f"Final population size: {dynamic_population}")
        logging.info("=" * 40)
        
        return dynamic_population
        
    except Exception as e:
        logging.warning(f"Dynamic population calculation failed: {e}")
        logging.warning("Using default population size: 100")  # Increased default
        return 100

def run_pynguin_standalone(module_name: str, seed_file: str, population_size: int):
    """Run Pynguin test generation with proper seed integration."""
    workspace_root = Path(__file__).parent
    
    # Prepare paths
    source_file = workspace_root / "tests" / "source" / f"{module_name}.py"
    output_dir = workspace_root / "tests" / "test_suites" / "pynguin_tests"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy source file to project root for Pynguin to import
    target_source = workspace_root / f"{module_name}.py"
    import shutil
    shutil.copy2(source_file, target_source)
    logging.info(f"Source file copied to: {target_source}")
    
    # Pynguin paths
    pynguin_path = workspace_root / "pynguin-main"
    pynguin_python = pynguin_path / "my_pynguin_venv" / "bin" / "python3"
    
    # Build Pynguin command with only seed test file path - use all Pynguin defaults
    cmd = [
        str(pynguin_python), "-m", "pynguin",
        "--project-path", str(workspace_root.resolve()),
        "--output-path", str(output_dir.resolve()),
        "--module-name", module_name,
        "--initial-population-seeding", "True",
        "--initial-population-data", str(Path(seed_file).parent.resolve()),
        "--verbose"
    ]
    
    # Environment setup
    env = os.environ.copy()
    env["PYTHONPATH"] = str(pynguin_path / "src") + ":" + env.get("PYTHONPATH", "")
    env["PYNGUIN_DANGER_AWARE"] = "1"
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    # Memory optimization
    env['PYTHONHASHSEED'] = '0'
    env['MALLOC_ARENA_MAX'] = '2'
    
    logging.info("=" * 60)
    logging.info("PYNGUIN EXECUTION CONFIGURATION")
    logging.info("=" * 60)
    logging.info(f"Command: {' '.join(cmd)}")
    logging.info(f"Working directory: {pynguin_path}")
    logging.info(f"Seed file: {seed_file}")
    logging.info(f"Source copied to: {target_source}")
    logging.info("Note: Using all Pynguin default settings except seed file")
    logging.info("=" * 60)
    
    # Execute Pynguin
    try:
        logging.info("Starting Pynguin execution...")
        
        import signal
        import time
        
        def timeout_handler(signum, frame):
            logging.error("Pynguin execution timed out - killing process")
            raise TimeoutError("Pynguin execution exceeded time limit")
        
        # Set timeout to 600 seconds (10 minutes) for default Pynguin execution
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(600)
        
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
        
        # Stream output in real-time with timeout protection
        output_lines = []
        start_time = time.time()
        while True:
            if time.time() - start_time > 590:  # Safety timeout (10 seconds before alarm)
                logging.warning("Approaching timeout, terminating process")
                process.terminate()
                time.sleep(2)
                if process.poll() is None:
                    process.kill()
                break
                
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                line = output.strip()
                output_lines.append(line)
                logging.info(f"PYNGUIN: {line}")
        
        signal.alarm(0)  # Cancel timeout
        return_code = process.poll()
        
        logging.info("=" * 60)
        logging.info("PYNGUIN EXECUTION COMPLETED")
        logging.info("=" * 60)
        logging.info(f"Return code: {return_code}")
        
        if return_code == 0:
            # Check for generated files
            generated_files = list(output_dir.glob("*.py"))
            if generated_files:
                logging.info("SUCCESS: Pynguin test generation completed!")
                logging.info("Generated files:")
                for file in generated_files:
                    file_size = file.stat().st_size
                    logging.info(f"  - {file.name} ({file_size} bytes)")
                return True
            else:
                logging.error("No test files generated")
                return False
        elif return_code == -9:
            logging.error("Pynguin was killed (likely out of memory or timeout)")
            logging.error("Try: Reducing population size, shortening timeout, or checking system memory")
            return False
        elif return_code == -15:
            logging.error("Pynguin was terminated (SIGTERM)")
            return False
        else:
            logging.error(f"Pynguin failed with return code: {return_code}")
            return False
            
    except TimeoutError:
        logging.error("Pynguin execution timed out")
        return False
            
    except Exception as e:
        logging.error(f"Exception during Pynguin execution: {e}")
        return False
    finally:
        # Cleanup copied source file
        if target_source.exists():
            target_source.unlink()
            logging.info(f"🧹 Cleaned up: {target_source}")

def main():
    """Main execution function."""
    if len(sys.argv) != 2:
        print("Usage: python standalone_pynguin.py <module_name>")
        print("Example: python standalone_pynguin.py sample_calculator_stats")
        print()
        print("Prerequisites:")
        print("1. Source file: tests/source/<module_name>.py")
        print("2. Seed file: tests/test_suites/test_<module_name>_seed.py")
        print("3. Pynguin environment: pynguin-main/my_pynguin_venv/")
        sys.exit(1)
    
    module_name = sys.argv[1]
    
    # Setup logging
    log_file = setup_simple_logging(module_name)
    
    # Check prerequisites
    if not check_prerequisites(module_name):
        logging.error("Prerequisites not met. Exiting.")
        sys.exit(1)
    
    # Calculate dynamic population
    population_size = calculate_dynamic_population(module_name)
    
    # Prepare seed file path
    seed_file = Path(__file__).parent / "tests" / "test_suites" / f"test_{module_name}_seed.py"
    
    # Run Pynguin
    success = run_pynguin_standalone(module_name, str(seed_file), population_size)
    
    if success:
        print(f"Pynguin test generation completed successfully for {module_name}")
        print(f"Output directory: tests/test_suites/pynguin_tests/")
        print(f"Log file: {log_file}")
    else:
        print(f"Pynguin test generation failed for {module_name}")
        print(f"Check log file: {log_file}")
        sys.exit(1)

if __name__ == "__main__":
    main()
