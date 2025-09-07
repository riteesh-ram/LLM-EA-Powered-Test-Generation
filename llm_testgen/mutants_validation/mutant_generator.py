#!/usr/bin/env python3
"""
Mutant Generator Module

This module handles the generation and separation of mutants using MutPy.
Single responsibility: Generate mutants from source code.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional
import logging


class MutantGenerator:
    """Handles mutant generation using MutPy."""
    
    def __init__(self, module_name: str, logger: Optional[logging.Logger] = None):
        #Initialize mutant generator.

        self.module_name = module_name
        self.logger = logger or logging.getLogger(__name__)
        
        # Define paths
        # When running from llm_testgen directory: python mutants_validation/pipeline_mutant_generator.py
        # Current working directory is llm_testgen, so we need to look in current directory for tests
        current_working_dir = Path.cwd()  # This is llm_testgen directory
        self.source_dir = current_working_dir / "tests" / "source"
        self.test_dir = current_working_dir / "tests" / "test_suites"
        self.mutants_dir = current_working_dir / "mutants_validation" / "generated_mutants"
        
        # File paths
        self.source_file = self.source_dir / f"{module_name}.py"
        self.test_file = self.test_dir / f"llm_generated_test_{module_name}.py"
        self.mutants_output = self.mutants_dir / f"mutants_all_{module_name}.txt"
        
        # MutPy environment paths - dynamic path resolution
        mutpy_env_dir = current_working_dir / "mutants_validation" / "mutpy_env"
        self.mutpy_python = str(mutpy_env_dir / "bin" / "python")
        self.mutpy_script = str(mutpy_env_dir / "bin" / "mut.py")
        
        # Validate that the mutpy environment exists
        if not Path(self.mutpy_python).exists():
            self.logger.warning(f"MutPy environment not found at: {self.mutpy_python}")
            self.logger.warning("Falling back to system Python and mut.py")
            self.mutpy_python = "python"
            self.mutpy_script = "mut.py"
        elif not Path(self.mutpy_script).exists():
            self.logger.warning(f"MutPy script not found at: {self.mutpy_script}")
            self.logger.warning("Falling back to system mut.py")
            self.mutpy_script = "mut.py"
    
    def generate_mutants(self) -> bool:
        """
        Generate mutants using MutPy.
        """
        # Ensure directories exist
        self.mutants_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate input files
        if not self.source_file.exists():
            self.logger.error(f"Source file not found: {self.source_file}")
            return False
        
        if not self.test_file.exists():
            self.logger.error(f"Test file not found: {self.test_file}")
            return False
        
        # Build MutPy command
        command = f'"{self.mutpy_python}" "{self.mutpy_script}" --target "{self.source_file}" --unit-test "{self.test_file}" -m > "{self.mutants_output}"'
        
        self.logger.info(f"Executing: {command}")
        
        try:
            # Execute mutation command
            result = subprocess.run(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            if result.returncode != 0:
                self.logger.error(f"Mutation command failed with return code: {result.returncode}")
                self.logger.error(f"stderr: {result.stderr.decode('utf-8')}")
                return False
            
            self.logger.info("Mutants generation completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing mutation command: {e}")
            return False
    
    def separate_mutants(self, csv_file_mut_type: str = "mutation_types_report.csv") -> bool:
        #Separate individual mutants from the combined MutPy output.

        csv_path = self.mutants_dir / csv_file_mut_type
        
        # Read original source code
        try:
            with open(self.source_file, 'r', encoding='utf-8') as file:
                org_data = file.readlines()
        except Exception as e:
            self.logger.error(f"Error reading source file {self.source_file}: {e}")
            return False
        
        # Check if mutants output exists
        if not self.mutants_output.exists():
            self.logger.error(f"Mutants output file not found: {self.mutants_output}")
            return False
        
        mutant_count = 0
        mut_type = "unknown"
        
        try:
            # Initialize CSV file with header
            with open(csv_path, 'w') as csv_file:
                csv_file.write("mutant_file,mutation_type\n")
            
            with open(self.mutants_output, 'r') as f:
                for ln in f:
                    ln = ln.lstrip(' ')
                    
                    # Parse mutation type
                    if ln.startswith("- [#"):
                        ln_mut = ln.split()
                        if len(ln_mut) > 3:
                            mut_type = ln_mut[3]
                    
                    # Parse mutant code lines
                    if ln.startswith("+"):
                        ln_partition = ln.split(":")
                        ln_num = (ln_partition[0][1:]).lstrip(' ')
                        ln_content = ln[6:]  # Content after "+ line_num: "
                        
                        # Create mutant by modifying the original code
                        temp = org_data[:]
                        temp[int(ln_num) - 1] = ln_content
                        
                        # Generate mutant file
                        mutant_name = f"mutant_{self.module_name}_{mutant_count}.py"
                        mutant_path = self.mutants_dir / mutant_name
                        
                        # Write mutant to file
                        with open(mutant_path, 'w') as mutant_file:
                            for item in temp:
                                mutant_file.write(item)
                        
                        # Record mutation type in CSV
                        with open(csv_path, 'a') as csv_file:
                            csv_file.write(f"{mutant_name},{mut_type}\n")
                        
                        mutant_count += 1
                        self.logger.info(f"Generated mutant: {mutant_name}")
            
            self.logger.info(f"Successfully generated {mutant_count} mutants for {self.module_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing mutants: {e}")
            return False
    
    def get_mutant_files(self) -> list[Path]:
        """
        Get list of generated mutant files.
        """
        mutant_pattern = f"mutant_{self.module_name}_*.py"
        return sorted(list(self.mutants_dir.glob(mutant_pattern)))
