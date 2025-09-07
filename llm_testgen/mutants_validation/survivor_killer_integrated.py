#!/usr/bin/env python3
"""
Integrated Survivor Killer for Mutation Testing Pipeline

This module generates killer tests for surviving mutants and integrates with 
the mutation testing pipeline using the existing test suite manager approach.
"""

import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any

# Add paths for imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir / "initial_test_suite_generation"))
sys.path.insert(0, str(parent_dir / "initial_test_suite_generation" / "generation"))
sys.path.insert(0, str(parent_dir / "initial_test_suite_generation" / "repair"))

from simple_llm import get_gemini_chat, send_prompt_to_llm
from test_suite_manager import TestSuiteManager
from mutant_diff_analyzer import MutantDiffAnalyzer


class SurvivorKillerIntegrated:
    """Integrated survivor killer that uses existing test suite manager approach."""
    
    def __init__(self):
        """Initialize with existing infrastructure."""
        self.logger = logging.getLogger(__name__)
        self.analyzer = MutantDiffAnalyzer()
        self.test_manager = TestSuiteManager()
        
        # Use existing chat session infrastructure
        try:
            self.chat_bot = get_gemini_chat()
            if not self.chat_bot.chat:
                raise RuntimeError("Gemini chat session not available")
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini chat: {e}")
            raise RuntimeError(f"Gemini chat session not available: {e}")
        
        # Set up paths - use the correct project structure
        self.project_root = Path(__file__).parent.parent  # llm_testgen directory
        self.source_dir = self.project_root / "tests" / "source"
        self.test_suites_dir = self.project_root / "tests" / "test_suites"
        
        self.logger.info(f"Project root: {self.project_root}")
        self.logger.info(f"Source dir: {self.source_dir}")
        self.logger.info(f"Test suites dir: {self.test_suites_dir}")
    
    def analyze_and_kill_survivors(self, source_name: str, surviving_mutants: List[str], 
                                 mutants_dir: Path) -> Dict:
        """
        Complete workflow: Analyze surviving mutants and generate killer tests.
        """
        try:
            # Set up file paths
            original_file = self.source_dir / f"{source_name}.py"
            existing_test_file = self.test_suites_dir / f"llm_generated_test_{source_name}.py"
            killer_test_file = self.test_suites_dir / f"mutants_killer_tests_{source_name}.py"
            
            self.logger.info(f"Original file: {original_file}")
            self.logger.info(f"Existing test file: {existing_test_file}")
            self.logger.info(f"Killer test file: {killer_test_file}")
            self.logger.info(f"Mutants directory: {mutants_dir}")
            
            # Verify files exist
            if not original_file.exists():
                return {'status': 'error', 'error': f'Source file not found: {original_file}'}
            if not existing_test_file.exists():
                return {'status': 'error', 'error': f'Test file not found: {existing_test_file}'}
            
            # 1. Analyze all surviving mutants
            self.logger.info(f"🔍 Analyzing {len(surviving_mutants)} surviving mutants...")
            mutant_analyses = []
            
            for mutant_name in surviving_mutants:
                mutant_file = mutants_dir / mutant_name
                if mutant_file.exists():
                    analysis = self.analyzer.analyze_mutant_diff(original_file, mutant_file)
                    mutant_analyses.append(analysis)
                    self.logger.info(f"   Analyzed: {mutant_name}")
            
            # 2. Generate killer tests using LLM
            self.logger.info("Generating killer tests with LLM...")
            killer_test_code = self._generate_killer_tests(
                source_name, original_file, existing_test_file, mutant_analyses
            )
            
            if not killer_test_code:
                return {'status': 'error', 'error': 'Failed to generate killer tests'}
            
            # 3. Save and run killer tests with repair mechanism
            self.logger.info("Saving killer tests and testing with repair...")
            test_results = self._save_and_test_killer_tests(
                killer_test_code, source_name, str(original_file), surviving_mutants, mutants_dir
            )
            
            # 4. If killer tests are successful, merge them with existing tests
            if test_results.get('success') and test_results.get('mutants_killed'):
                self.logger.info("Merging killer tests with existing test suite...")
                merge_results = self._merge_killer_tests_with_existing(source_name, killer_test_file)
                test_results['merge_results'] = merge_results
            
            return {
                'status': 'success',
                'mutant_analyses': mutant_analyses,
                'killer_test_file': str(killer_test_file),
                'total_mutants_analyzed': len(mutant_analyses),
                'test_results': test_results,
                'killer_tests_working': test_results.get('success', False)
            }
            
        except Exception as e:
            self.logger.error(f"Error in analyze_and_kill_survivors: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _generate_killer_tests(self, source_name: str, original_file: Path, 
                              existing_test_file: Path, mutant_analyses: List[Dict]) -> str:
        """Generate killer tests using LLM with file uploads."""
        
        # Generate prompt without embedding file contents
        prompt = self._build_killer_test_prompt_with_uploads(source_name, mutant_analyses)
        
        # Log the prompt being sent to LLM
        self.logger.info("PROMPT BEING SENT TO LLM:")
        self.logger.info("=" * 80)
        self.logger.info(prompt)
        self.logger.info("=" * 80)
        
        # Call LLM with file uploads
        try:
            response = self._send_killer_test_request_with_files(prompt, original_file, existing_test_file)
            if response:
                self.logger.info("Successfully received killer tests from LLM")
                return response
            else:
                self.logger.error("No response from LLM")
                return None
        except Exception as e:
            self.logger.error(f"Error calling LLM: {e}")
            return None
    
    def _send_killer_test_request_with_files(self, prompt: str, original_file: Path, existing_test_file: Path) -> str:
        """Send killer test request with uploaded files."""
        try:
            import google.generativeai as genai
            
            # Upload source file
            self.logger.info(f"Uploading source file: {original_file}")
            source_file_upload = genai.upload_file(str(original_file))
            
            # Upload existing test file
            self.logger.info(f"Uploading existing test file: {existing_test_file}")
            test_file_upload = genai.upload_file(str(existing_test_file))
            
            # Send message with uploaded files and prompt
            response = self.chat_bot.chat.send_message([
                "Source Code File (original implementation):",
                source_file_upload,
                "Existing Test Suite File (for reference structure and style):",
                test_file_upload,
                prompt
            ])
            
            return response.text.strip() if response and response.text else None
            
        except Exception as e:
            self.logger.error(f"File upload failed, falling back to embedded approach: {e}")
            # Fallback to embedded content approach
            return self._fallback_killer_test_request(prompt, original_file, existing_test_file)
    
    def _fallback_killer_test_request(self, prompt: str, original_file: Path, existing_test_file: Path) -> str:
        """Fallback method: include file contents in prompt if upload fails."""
        try:
            source_content = original_file.read_text(encoding='utf-8')
            existing_test_content = existing_test_file.read_text(encoding='utf-8')
            
            # Create fallback prompt with embedded files
            fallback_prompt = f"""You are an expert at generating targeted test cases to kill specific mutants in mutation testing.

SOURCE CODE FILE (original implementation):
```python
{source_content}
```

EXISTING TEST SUITE FILE (for reference structure and style):
```python
{existing_test_content}
```

{prompt}"""
            
            response = self.chat_bot.send_message(fallback_prompt)
            return response.strip() if response else None
            
        except Exception as e:
            self.logger.error(f"Fallback killer test request failed: {e}")
            return None

    def _build_killer_test_prompt_with_uploads(self, source_name: str, mutant_analyses: List[Dict]) -> str:
        """Build prompt for killer test generation with file uploads (no embedded content)."""
        
        prompt_parts = [
            "# MUTATION TESTING KILLER TEST GENERATION",
            "",
            "You are an expert at generating targeted test cases to kill specific mutants in mutation testing.",
            "Your task is to create killer tests that will PASS on the original source code but FAIL on the surviving mutants.",
            "",
            "I have uploaded two files:",
            "1. **Source Code File**: The original implementation that you need to test",
            "2. **Existing Test Suite File**: For reference on import structure, style, and testing patterns",
            "",
            "## CRITICAL REQUIREMENTS:",
            "",
            "1. **File Structure**: Save as `mutants_killer_tests_{source_name}.py` in tests/test_suites/",
            "2. **Import Structure**: Follow the exact same pattern as the existing test file",
            "3. **Test Behavior**: Tests MUST pass on original source, MUST fail on mutants",
            "4. **Naming**: Use descriptive test names like `test_kill_mutant_[description]`",
            "",
            "## SURVIVING MUTANTS TO KILL:",
            ""
        ]
        
        # Add detailed mutant analysis
        for i, analysis in enumerate(mutant_analyses, 1):
            mutant_name = analysis.get('mutant_file', f'mutant_{i}')
            prompt_parts.extend([
                f"### Mutant {i}: {mutant_name}",
                ""
            ])
            
            if 'error' in analysis:
                prompt_parts.append(f"Error analyzing: {analysis['error']}")
                continue
            
            changes = analysis.get('changes', [])
            if changes:
                prompt_parts.append("**Changes made:**")
                for change in changes:
                    line_num = change.get('line_number')
                    change_type = change.get('change_type')
                    original = change.get('original', '')
                    mutated = change.get('mutated', '')
                    
                    if change_type == 'modified':
                        prompt_parts.append(f"- Line {line_num}: `{original}` → `{mutated}`")
                    elif change_type == 'deleted':
                        prompt_parts.append(f"- Line {line_num}: Deleted `{original}`")
                    elif change_type == 'inserted':
                        prompt_parts.append(f"- Line {line_num}: Inserted `{mutated}`")
                
                prompt_parts.append("")
        
        # Add generation instructions
        prompt_parts.extend([
            "## YOUR TASK:",
            "",
            "Generate a complete killer test file with the following structure:",
            "",
            "```python",
            "import pytest",
            "import sys", 
            "from pathlib import Path",
            "from unittest.mock import Mock, call",
            "import runpy",
            "import importlib",
            "",
            "# Add the tests/source directory to Python path",
            "current_dir = Path(__file__).parent",
            "source_dir = current_dir.parent / \"source\"",
            "sys.path.insert(0, str(source_dir))",
            "",
            f"import {source_name}",
            f"from {source_name} import classify_numbers  # Import main function",
            "",
            "class TestKillerMutants:",
            "    \"\"\"Killer tests for surviving mutants.\"\"\"",
            "",
            "    def test_kill_mutant_[description](self, monkeypatch):",
            "        \"\"\"Docstring explaining what mutant this kills.\"\"\"",
            "        # Test implementation that passes on original, fails on mutant",
            "        pass",
            "```",
            "",
            "## KILLER TEST STRATEGIES:",
            "",
            "1. **Main Guard Mutations**: Use module execution testing with runpy or importlib.reload",
            "2. **Value Mutations**: Test exact values that expose the mutation",
            "3. **Operator Mutations**: Test boundary conditions that reveal operator changes",
            "4. **Logic Mutations**: Test specific control flow scenarios",
            "",
            "## EXAMPLE APPROACHES:",
            "",
            "- For main block mutations: Force execution and check side effects",
            "- For value changes: Assert exact expected values or outputs",
            "- For guard inversions: Test import vs execution behavior",
            "",
            "Generate the complete killer test file now based on the uploaded source code and existing test file:"
        ])
        
        return "\n".join(prompt_parts)
    
    def _save_and_test_killer_tests(self, killer_test_code: str, source_name: str, 
                                   source_file_path: str, surviving_mutants: List[str], 
                                   mutants_dir: Path) -> Dict:
        """Save killer tests and test them with repair mechanism."""
        
        # Create killer test filename
        killer_test_filename = f"mutants_killer_tests_{source_name}.py"
        killer_test_path = self.test_suites_dir / killer_test_filename
        
        self.logger.info(f"Saving killer tests as: {killer_test_path}")
        
        # Save initial killer test file
        try:
            cleaned_code = self.test_manager._clean_test_code(killer_test_code)
            with open(killer_test_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_code)
            self.logger.info(f"Killer test file saved: {killer_test_path}")
        except Exception as e:
            self.logger.error(f"Failed to save killer test file: {e}")
            return {'success': False, 'error': f'Failed to save killer test file: {e}'}
        
        # Test with repair mechanism (5 attempts)
        source_dir = os.path.dirname(source_file_path)
        attempt = 0
        max_repair_attempts = 5
        
        while attempt <= max_repair_attempts:
            if attempt > 0:
                self.logger.info(f"\nRepair attempt {attempt}/{max_repair_attempts}")
            
            # Run tests on current killer test file
            results = self.test_manager.run_tests(str(killer_test_path), source_dir)
            
            if results['success']:
                self.logger.info(f"Killer tests passed on original source on attempt {attempt + 1}!")
                
                # Now test against surviving mutants
                mutant_test_results = self._test_against_mutants(
                    killer_test_path, source_file_path, surviving_mutants, mutants_dir
                )
                
                results.update(mutant_test_results)
                return results
            
            if attempt >= max_repair_attempts:
                self.logger.error(f"Killer test repair failed after {max_repair_attempts} attempts")
                return results
            
            # Get repaired code from LLM
            self.logger.info(f"Attempting to repair killer tests (attempt {attempt + 1})...")
            repaired_code = self._repair_killer_tests_with_llm(results['output'], source_name)
            
            if repaired_code:
                try:
                    cleaned_repaired_code = self.test_manager._clean_test_code(repaired_code)
                    with open(killer_test_path, 'w', encoding='utf-8') as f:
                        f.write(cleaned_repaired_code)
                    self.logger.info(f"Killer test file overwritten with repaired code")
                    attempt += 1
                except Exception as e:
                    self.logger.error(f"Failed to overwrite killer test file: {e}")
                    return results
            else:
                self.logger.error("Could not repair killer tests, stopping")
                return results
                
        return results
    
    def _repair_killer_tests_with_llm(self, error_output: str, source_name: str) -> str:
        """Send error output to LLM for killer test repair."""
        try:
            repair_prompt = f"""
The killer test execution failed with the following error:

ERROR OUTPUT:
```
{error_output}
```

Please regenerate the complete killer test suite that fixes these issues.

CRITICAL REQUIREMENTS:
1. **File Structure**: This is a killer test file for {source_name}.py
2. **Import Structure**: ALWAYS start with these exact lines:
   ```python
   import pytest
   import sys
   from pathlib import Path
   from unittest.mock import Mock, call
   import runpy
   import importlib
   
   # Add the tests/source directory to Python path
   current_dir = Path(__file__).parent
   source_dir = current_dir.parent / "source"
   sys.path.insert(0, str(source_dir))
   
   import {source_name}
   from {source_name} import classify_numbers
   ```
3. **Test Behavior**: Tests MUST pass on original source, MUST fail on mutants
4. **Class Structure**: Use `class TestKillerMutants:` with proper test methods
5. **Naming**: Use descriptive test names like `test_kill_mutant_[description]`

Fix all syntax errors, import issues, and test logic problems.
Return ONLY the corrected Python test code without markdown formatting.

Generate the complete corrected killer test code:
"""
            
            self.logger.info("🔧 Sending killer test repair request to LLM...")
            self.logger.info("REPAIR PROMPT BEING SENT TO LLM:")
            self.logger.info("=" * 80)
            self.logger.info(repair_prompt[:1000] + "..." if len(repair_prompt) > 1000 else repair_prompt)
            self.logger.info("=" * 80)
            repaired_code = self.chat_bot.send_message(repair_prompt)
            
            if repaired_code:
                self.logger.info("Killer test repair completed")
                return repaired_code
            else:
                self.logger.error("Killer test repair failed")
                return None
                
        except Exception as e:
            self.logger.error(f"Killer test repair error: {e}")
            return None
    
    def _test_against_mutants(self, killer_test_file: Path, source_file_path: str,
                             surviving_mutants: List[str], mutants_dir: Path) -> Dict:
        """Test killer tests against surviving mutants."""
        
        results = {
            'mutants_killed': [],
            'mutants_still_surviving': [],
            'mutant_test_details': {}
        }
        
        self.logger.info(f"Testing killer tests against {len(surviving_mutants)} surviving mutants...")
        self.logger.info(f"Mutants directory: {mutants_dir}")
        self.logger.info(f"Mutants directory exists: {mutants_dir.exists()}")
        self.logger.info(f"Mutants directory is absolute: {mutants_dir.is_absolute()}")
        
        if mutants_dir.exists():
            all_mutants = list(mutants_dir.glob("mutant_*.py"))
            self.logger.info(f"All mutant files found: {[f.name for f in all_mutants]}")
        else:
            self.logger.error(f"Mutants directory does not exist: {mutants_dir}")
        
        # Get source file path
        source_file = Path(source_file_path)
        backup_content = source_file.read_text()
        
        for mutant_name in surviving_mutants:
            mutant_file = mutants_dir / mutant_name
            if not mutant_file.exists():
                self.logger.warning(f"Mutant file not found: {mutant_file}")
                continue
            
            self.logger.info(f"   Testing against: {mutant_name}")
            
            try:
                # Replace source with mutant content
                mutant_content = mutant_file.read_text()
                source_file.write_text(mutant_content)
                
                # Run killer tests against mutant
                mutant_results = self.test_manager.run_tests(str(killer_test_file))
                
                if mutant_results['success']:
                    # Tests passed on mutant = mutant survived
                    self.logger.warning(f" Mutant {mutant_name} still SURVIVES")
                    results['mutants_still_surviving'].append(mutant_name)
                else:
                    # Tests failed on mutant = mutant killed
                    self.logger.info(f"  Mutant {mutant_name} KILLED")
                    results['mutants_killed'].append(mutant_name)
                
                results['mutant_test_details'][mutant_name] = {
                    'killed': not mutant_results['success'],
                    'output': mutant_results['output']
                }
                
            except Exception as e:
                self.logger.error(f"  Error testing {mutant_name}: {e}")
                results['mutant_test_details'][mutant_name] = {
                    'killed': False,
                    'error': str(e)
                }
            finally:
                # Restore original source
                source_file.write_text(backup_content)
        
        # Summary
        killed_count = len(results['mutants_killed'])
        surviving_count = len(results['mutants_still_surviving'])
        
        self.logger.info(f"Killer test results: {killed_count} killed, {surviving_count} still surviving")
        
        if surviving_count == 0:
            self.logger.info("All surviving mutants have been killed!")
        else:
            self.logger.warning(f"{surviving_count} mutants still surviving: {results['mutants_still_surviving']}")
        
        return results
    
    def _merge_killer_tests_with_existing(self, source_name: str, killer_test_file: Path) -> Dict:
        """Merge killer tests into the existing LLM-generated test suite."""
        try:
            existing_test_file = self.test_suites_dir / f"llm_generated_test_{source_name}.py"
            
            if not existing_test_file.exists():
                return {'success': False, 'error': f'Existing test file not found: {existing_test_file}'}
            
            if not killer_test_file.exists():
                return {'success': False, 'error': f'Killer test file not found: {killer_test_file}'}
            
            self.logger.info(f"Merging {killer_test_file} into {existing_test_file}")
            
            # Create backup of existing test file
            backup_file = existing_test_file.with_suffix('.py.backup_before_merge')
            existing_content = existing_test_file.read_text(encoding='utf-8')
            backup_file.write_text(existing_content, encoding='utf-8')
            self.logger.info(f"Created backup: {backup_file}")
            
            # Read killer tests
            killer_content = killer_test_file.read_text(encoding='utf-8')
            
            # Generate merge prompt and call LLM
            merge_prompt = self._build_merge_prompt(source_name)
            
            self.logger.info("Sending merge request to LLM...")
            self.logger.info("MERGE PROMPT BEING SENT TO LLM:")
            self.logger.info("=" * 80)
            self.logger.info(merge_prompt[:1000] + "..." if len(merge_prompt) > 1000 else merge_prompt)
            self.logger.info("=" * 80)
            
            # Call LLM with file uploads for merging
            merged_content = self._send_merge_request_with_files(merge_prompt, existing_test_file, killer_test_file)
            
            if not merged_content:
                return {'success': False, 'error': 'Failed to get merged content from LLM'}
            
            # Clean and save merged content
            cleaned_merged_content = self.test_manager._clean_test_code(merged_content)
            existing_test_file.write_text(cleaned_merged_content, encoding='utf-8')
            
            self.logger.info(f"Successfully merged killer tests into: {existing_test_file}")
            
            # Test the merged file
            self.logger.info("Testing merged test suite...")
            source_dir = str(self.source_dir)
            merged_test_results = self.test_manager.run_tests(str(existing_test_file), source_dir)
            
            return {
                'success': True,
                'merged_file': str(existing_test_file),
                'backup_file': str(backup_file),
                'merged_test_results': merged_test_results
            }
            
        except Exception as e:
            self.logger.error(f"Error merging killer tests: {e}")
            return {'success': False, 'error': str(e)}
    
    def _build_merge_prompt(self, source_name: str) -> str:
        """Build prompt for merging killer tests with existing test suite."""
        
        prompt = f"""You are an expert software testing engineer. I need you to merge two test suites for the same Python module:

I have uploaded two files:
1. **Existing LLM Test Suite** (first file): The main comprehensive test suite
2. **Killer Tests Suite** (second file): Specialized tests designed to kill surviving mutants

**Your Task:**
Please merge these test suites by adding all the killer test methods and their imports to the existing LLM test suite.

**Guidelines:**
1. **Keep the existing test structure** - maintain the original class-based format and existing test methods
2. **Add all killer test methods** - copy all test methods from the killer test suite
3. **Merge imports** - combine all import statements, removing duplicates
4. **Maintain naming** - keep all original test method names and add the killer test methods
5. **Preserve functionality** - ensure all tests (original + killer) work together
6. **Single class structure** - merge everything into one main test class
7. **Keep docstrings** - preserve all documentation and comments

**Critical Requirements:**
- Return the complete merged test suite
- Include ALL test methods from both files
- Ensure proper import statements at the top
- Maintain pytest compatibility
- Use descriptive test method names
- Keep the existing test class name (like `TestSampleNumber`)

**Output Requirements:**
- Complete Python test file that can be run with pytest
- All imports at the top (no duplicates)
- Single test class containing all test methods
- Proper formatting and indentation
- All original tests + all killer tests working together

Please provide the complete merged test suite for {source_name}:"""

        return prompt
    
    def _send_merge_request_with_files(self, prompt: str, existing_test_file: Path, killer_test_file: Path) -> str:
        """Send merge request with uploaded test files."""
        try:
            import google.generativeai as genai
            
            # Upload existing test file
            self.logger.info(f"Uploading existing test file: {existing_test_file}")
            existing_file_upload = genai.upload_file(str(existing_test_file))
            
            # Upload killer test file
            self.logger.info(f"Uploading killer test file: {killer_test_file}")
            killer_file_upload = genai.upload_file(str(killer_test_file))
            
            # Send message with uploaded files and prompt
            response = self.chat_bot.chat.send_message([
                "Existing LLM Test Suite:",
                existing_file_upload,
                "Killer Tests Suite:",
                killer_file_upload,
                prompt
            ])
            
            return response.text.strip() if response and response.text else None
            
        except Exception as e:
            self.logger.error(f"File upload failed, falling back to embedded approach: {e}")
            # Fallback to embedded content approach
            return self._fallback_merge_request(prompt, existing_test_file, killer_test_file)
    
    def _fallback_merge_request(self, prompt: str, existing_test_file: Path, killer_test_file: Path) -> str:
        """Fallback method: include test files in prompt if upload fails."""
        try:
            existing_content = existing_test_file.read_text(encoding='utf-8')
            killer_content = killer_test_file.read_text(encoding='utf-8')
            
            # Create fallback prompt with embedded files
            fallback_prompt = f"""You are an expert software testing engineer. I need you to merge two test suites:

EXISTING LLM TEST SUITE:
```python
{existing_content}
```

KILLER TESTS SUITE:
```python
{killer_content}
```

{prompt}"""
            
            response = self.chat_bot.send_message(fallback_prompt)
            return response.strip() if response else None
            
        except Exception as e:
            self.logger.error(f"Fallback merge request failed: {e}")
            return None
def main():
    """Test the integrated survivor killer."""
    logging.basicConfig(level=logging.INFO)
    
    # Test with sample_number
    source_name = "sample_number"
    surviving_mutants = [
        "mutant_sample_number_0.py",
        "mutant_sample_number_1.py", 
        "mutant_sample_number_8.py",
        "mutant_sample_number_14.py"
    ]
    mutants_dir = Path("generated_mutants")
    
    try:
        killer = SurvivorKillerIntegrated()
        result = killer.analyze_and_kill_survivors(source_name, surviving_mutants, mutants_dir)
        
        if result['status'] == 'success':
            print(f"\nAnalysis complete! Analyzed {result['total_mutants_analyzed']} mutants")
            print(f"Killer test file: {result['killer_test_file']}")
            print(f"Killer tests working: {result['killer_tests_working']}")
        else:
            print(f"Error: {result['error']}")
            
    except Exception as e:
        print(f"Failed to initialize: {e}")


if __name__ == "__main__":
    main()
