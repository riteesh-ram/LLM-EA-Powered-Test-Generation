#!/usr/bin/env python3
"""
Test script for ASTER-style static analysis pipeline. This script tests the complete analysis pipeline by:
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import our modules
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))
sys.path.insert(0, str(current_dir))  # Add analysis directory to path

from analysis.module_parser import parse_python_module
from analysis.function_extractor import extract_top_level_functions
from analysis.class_extractor import extract_classes
from analysis.import_extractor import extract_imports
from analysis.monkeypatch_extractor import identify_monkeypatch_points
from analysis.prompt_formatter import create_full_aster_prompt


def generate_tests_with_llm(prompt: str, source_file_path: str = None) -> tuple:
    #Generate tests using Gemini LLM and save to file with automatic repair.
    try:
        current_dir = Path(__file__).parent
        generation_dir = current_dir.parent / "generation"
        repair_dir = current_dir.parent / "repair"
        sys.path.insert(0, str(generation_dir))
        sys.path.insert(0, str(repair_dir))
        from generation.simple_llm import send_prompt_to_llm
        from repair.test_suite_manager import get_test_manager
        
        print("Generating tests with Gemini...")
        
        # Log the complete prompt before sending to LLM
        print("\n" + "=" * 80)
        print("COMPLETE PROMPT BEING SENT TO LLM")
        print("=" * 80)
        print(prompt)
        print("=" * 80)
        print(f"Prompt length: {len(prompt)} characters")
        print("=" * 80 + "\n")
        
        generated_tests = send_prompt_to_llm(prompt, source_file_path)
        
        if generated_tests:
            print("Tests generated successfully")
            
            # Save test suite to file and run with repair
            if source_file_path:
                test_manager = get_test_manager()
                source_filename = os.path.basename(source_file_path)
                
                # Use the new repair functionality with default max_repair_attempts from config
                results = test_manager.save_and_run_tests_with_repair(
                    generated_tests, source_filename, source_file_path
                )
                test_manager.print_test_results(results)
                
                # Get the final test file path with new naming convention
                base_name = source_filename.replace('.py', '')
                test_filename = f"llm_generated_test_{base_name}.py"
                test_file_path = str(test_manager.test_dir / test_filename)
                
                return generated_tests, test_file_path, results
            else:
                return generated_tests, None, None
        else:
            print("No tests generated")
            return None, None, None
            
    except ImportError as e:
        print(f"Import error: {e}")
        return None, None, None
    except Exception as e:
        print(f"Generation failed: {e}")
        return None, None, None


def test_single_module(module_path: str, verbose: bool = True):
    #Test analysis pipeline on a single module.
    print(f"\nAnalyzing: {os.path.basename(module_path)}")
    
    try:
        # Read source code
        with open(module_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        print(f"Source loaded ({len(source_code)} chars)")
        
        # Parse AST
        tree = parse_python_module(module_path)
        print("AST parsed")
        
        # Extract components
        functions = extract_top_level_functions(tree)
        classes = extract_classes(tree)
        imports = extract_imports(tree)
        monkeypatch_points = identify_monkeypatch_points(tree)
        
        if verbose:
            print(f"Found: {len(functions)} functions, {len(classes)} classes, {len(imports.get('import_statements', []))} imports")
        
        # Generate ASTER prompt
        module_name = os.path.basename(module_path).replace('.py', '')
        prompt = create_full_aster_prompt(
            module_source=source_code,
            functions=functions,
            classes=classes,
            imports=imports,
            monkeypatch_points=monkeypatch_points,
            module_name=module_name,
            include_docstrings=True,
            include_type_annotations=True,
            include_source_in_prompt=False  # Don't include source since we upload the file
        )
        
        print(f"Generated prompt ({len(prompt)} chars)")
        return prompt
        
    except Exception as e:
        print(f"Error analyzing {module_path}: {e}")
        return None


def run_all_tests():
    #Run analysis on all Python files in tests/source.
    current_dir = Path(__file__).parent
    source_dir = current_dir.parent.parent / "tests" / "source"
    
    if not source_dir.exists():
        source_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created: {source_dir}")
    
    sample_files = [f for f in source_dir.glob("*.py") if f.is_file() and not f.name.startswith("__")]
    
    if not sample_files:
        print(f"No Python files found in {source_dir}")
        return
    
    print(f"Testing {len(sample_files)} files")
    results = {}
    
    for sample_file in sample_files:
        print(f"\n{'='*50}")
        prompt = test_single_module(str(sample_file), verbose=True)
        
        if prompt:
            results[sample_file.name] = prompt
            print(f"\nASTER Prompt for {sample_file.name}:")
            print("-" * 40)
            print(prompt)
            print("-" * 40)
            
            # Generate tests and run them
            generated_tests, test_file_path, test_results = generate_tests_with_llm(prompt, str(sample_file))
            if generated_tests:
                print(f"\nGenerated Tests Preview:")
                print("-" * 40)
                print(generated_tests[:300] + "..." if len(generated_tests) > 300 else generated_tests)
                
                if test_file_path:
                    print(f"\nTest file saved: {test_file_path}")
                    if test_results and test_results['success']:
                        print("All tests passed!")
                    elif test_results:
                        print("Some tests failed - see results above")
        else:
            print(f"Failed: {sample_file.name}")
    
    print(f"\nSummary: {len(results)}/{len(sample_files)} successful")
    return results


def main():
    #Main entry point.
    print("ASTER Pipeline Test")
    print("=" * 30)
    
    if len(sys.argv) > 1:
        module_path = sys.argv[1]
        
        # Check if file exists in tests/source
        if not os.path.sep in module_path and not os.path.exists(module_path):
            current_dir = Path(__file__).parent
            potential_path = current_dir.parent / "tests" / "source" / module_path
            if potential_path.exists():
                module_path = str(potential_path)
                print(f"Found: {module_path}")
        
        if os.path.exists(module_path):
            prompt = test_single_module(module_path)
            if prompt:
                print(f"\nASTER Prompt:")
                print("-" * 30)
                print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
                
                # Generate tests and run them
                generated_tests, test_file_path, test_results = generate_tests_with_llm(prompt, module_path)
                if generated_tests:
                    print(f"\nGenerated Tests:")
                    print("-" * 30)
                    print(generated_tests[:500] + "..." if len(generated_tests) > 500 else generated_tests)
                    
                    if test_file_path:
                        print(f"\nTest file: {test_file_path}")
                        if test_results and test_results['success']:
                            print("All tests passed!")
                        elif test_results:
                            print("Some tests failed - see results above")
        else:
            print(f"File not found: {module_path}")
    else:
        run_all_tests()


class TestGenerationPipeline:
    """Pipeline for orchestrating test generation from initial analysis to final tests."""
    
    def __init__(self, config=None):
        """Initialize the test generation pipeline."""
        self.config = config
        print("TestGenerationPipeline initialized")
    
    def generate_test_suite(self):
        """Generate test suite for the configured module - main entry point."""
        if not self.config:
            print("No configuration provided")
            return []
        
        # Build source file path
        source_file_path = os.path.join(self.config.source_dir, f"{self.config.module_name}.py")
        
        if not os.path.exists(source_file_path):
            print(f"Source file not found: {source_file_path}")
            return []
        
        print(f"Generating test suite for: {source_file_path}")
        
        # Run the pipeline
        result = self.run_pipeline(source_file_path)
        
        if result and result.get('test_file_path'):
            return [result['test_file_path']]
        else:
            return []
    
    def run_pipeline(self, source_file_path: str):
        """Run the complete test generation pipeline."""
        print(f"Running test generation pipeline for: {source_file_path}")
        
        # Generate prompt using existing analysis
        prompt = test_single_module(source_file_path, verbose=True)
        if not prompt:
            print(f"Failed to generate prompt for {source_file_path}")
            return None
        # Generate tests with LLM
        generated_tests, test_file_path, test_results = generate_tests_with_llm(prompt, source_file_path)
        
        if generated_tests:
            print(f"Test generation completed successfully")
            return {
                'prompt': prompt,
                'generated_tests': generated_tests,
                'test_file_path': test_file_path,
                'test_results': test_results
            }
        else:
            print(f"Test generation failed")
            return None


if __name__ == "__main__":
    main()
