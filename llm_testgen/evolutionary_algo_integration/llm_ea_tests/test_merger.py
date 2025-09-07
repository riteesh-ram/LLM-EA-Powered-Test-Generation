#!/usr/bin/env python3
"""
Test Merger: Combines LLM and Pynguin generated test suites.
This script sends both test suites to LLM to identify missing edge cases and merge them.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "initial_test_suite_generation"))

from generation.simple_llm import send_prompt_to_llm, get_gemini_chat


class TestSuiteMerger:
    """Merges LLM and Pynguin generated test suites using LLM analysis."""
    
    def __init__(self, source_file_name):
        #Initialize the merger for a specific source file.
        self.source_file_name = source_file_name
        
        # Define file paths
        self.test_suites_dir = project_root / "tests" / "test_suites"
        self.llm_test_file = self.test_suites_dir / f"llm_generated_test_{source_file_name}.py"
        self.pynguin_test_file = self.test_suites_dir / "pynguin_tests" / f"pynguin_generated_test_{source_file_name}.py"
        self.seed_file = self.test_suites_dir / f"llm_generated_test_{source_file_name}_seed.py"  # Avoid this
        
        # Verify files exist
        self._verify_files()
    
    def _verify_files(self):
        """Verify that required test files exist."""
        if not self.llm_test_file.exists():
            raise FileNotFoundError(f"LLM test file not found: {self.llm_test_file}")
        
        if not self.pynguin_test_file.exists():
            raise FileNotFoundError(f"Pynguin test file not found: {self.pynguin_test_file}")
        
        print(f"Found LLM test file: {self.llm_test_file}")
        print(f"Found Pynguin test file: {self.pynguin_test_file}")
        
        # Check if seed file exists (we should NOT use this)
        if self.seed_file.exists():
            print(f"Seed file detected (will be ignored): {self.seed_file}")
    
    def _create_merge_prompt(self):
        """Create the prompt for LLM to merge test suites (files will be uploaded separately)."""
        
        prompt = """You are an expert software testing engineer. I have uploaded two test suites for the same Python module:

1. **LLM-Generated Test Suite** (first file): Human-readable, well-structured test suite
2. **EA/Pynguin-Generated Test Suite** (second file): Evolutionary Algorithm generated tests that may contain edge cases

**Your Task:**
Please review the EA/Pynguin-generated test suite in detail and:

a. **Identify any test cases present in the EA suite that are missing from our initial LLM test suite**
b. **For each missing test case, add it to our final test suite, ensuring no duplication and maintaining code quality**
c. **Focus on edge cases, boundary conditions, and error scenarios that the EA suite discovered**

**Guidelines:**
1. **Maintain the existing LLM test structure** - keep the well-organized class-based format with descriptive test names
2. **Add meaningful test cases only** - ignore tests that are purely random or don't add value
3. **Convert EA tests to human-readable format** - use descriptive names and comments
4. **Ensure pytest compatibility** - all tests should be runnable with pytest
5. **Handle invalid inputs properly** - if EA tests invalid types, add proper error handling tests
6. **Avoid duplication** - don't add tests that are essentially the same as existing ones
7. **Keep the imports and setup from the LLM version** - maintain the same module import structure

**Output Requirements:**
- Return the complete merged test suite
- Include all original LLM tests (unchanged)
- Add new test methods for any valuable edge cases from EA suite
- Use clear, descriptive test method names
- Add docstrings explaining what each new test covers
- Ensure the final code is clean, readable, and professionally formatted

Please provide the complete merged test suite that combines the best of both approaches."""

        return prompt
    
    def merge_test_suites(self):
        """Main method to merge the test suites using LLM with file uploads."""
        print("Starting test suite merge process...")
        
        # Create merge prompt (files will be uploaded separately)
        merge_prompt = self._create_merge_prompt()
        
        print("Sending merge request to LLM...")
        print(f"Prompt length: {len(merge_prompt)} characters")
        print(f"Uploading LLM test file: {self.llm_test_file}")
        print(f"Uploading Pynguin test file: {self.pynguin_test_file}")
        
        # Use the existing LLM function with file upload capability
        # We'll use a modified approach to upload multiple files
        merged_tests = self._send_merge_request_with_files(merge_prompt)
        
        if not merged_tests:
            print("Failed to get response from LLM")
            return False
        
        print("Received merged test suite from LLM")
        print(f"Response length: {len(merged_tests)} characters")
        
        # Save the merged test suite
        return self._save_merged_tests(merged_tests)
    
    def _send_merge_request_with_files(self, prompt):
        """Send merge request with both test files uploaded to LLM."""
        try:
            import google.generativeai as genai
            
            # Get the chat bot instance
            chat_bot = get_gemini_chat()
            
            # Upload both test files
            print("Uploading LLM test file...")
            llm_file = genai.upload_file(str(self.llm_test_file))
            
            print("Uploading Pynguin test file...")
            pynguin_file = genai.upload_file(str(self.pynguin_test_file))
            
            # Send message with both files and prompt
            response = chat_bot.chat.send_message([
                "LLM Test Suite:",
                llm_file,
                "Pynguin Test Suite:",
                pynguin_file,
                prompt
            ])
            
            return response.text.strip() if response and response.text else None
            
        except Exception as e:
            print(f"File upload failed, falling back to prompt-based approach: {e}")
            # Fallback: read files and include in prompt
            return self._fallback_merge_request(prompt)
    
    def _fallback_merge_request(self, prompt):
        """Fallback method: include test files in prompt if upload fails."""
        try:
            # Read both test files
            with open(self.llm_test_file, 'r', encoding='utf-8') as f:
                llm_tests = f.read()
            
            with open(self.pynguin_test_file, 'r', encoding='utf-8') as f:
                pynguin_tests = f.read()
            
            print(f"Read LLM tests: {len(llm_tests)} characters")
            print(f"Read Pynguin tests: {len(pynguin_tests)} characters")
            
            # Create fallback prompt with embedded files
            fallback_prompt = f"""You are an expert software testing engineer. I have two test suites for the same Python module:

1. **LLM-Generated Test Suite (Human-readable, well-structured)**:
```python
{llm_tests}
```

2. **EA/Pynguin-Generated Test Suite (Evolutionary Algorithm, may contain edge cases)**:
```python
{pynguin_tests}
```

{prompt}"""
            
            # Use the existing send_prompt_to_llm function
            return send_prompt_to_llm(fallback_prompt)
            
        except Exception as e:
            print(f"Fallback merge request failed: {e}")
            return None
    
    def _save_merged_tests(self, merged_tests):
        """Save the merged test suite back to the LLM test file."""
        try:
            # Create backup of original LLM tests
            backup_file = self.llm_test_file.with_suffix('.py.backup')
            with open(backup_file, 'w', encoding='utf-8') as f:
                with open(self.llm_test_file, 'r', encoding='utf-8') as original:
                    f.write(original.read())
            print(f"Created backup: {backup_file}")
            
            # Clean up the merged tests (remove markdown code blocks if present)
            cleaned_tests = self._clean_llm_response(merged_tests)
            
            # Save merged tests to the original LLM test file
            with open(self.llm_test_file, 'w', encoding='utf-8') as f:
                f.write(cleaned_tests)
            
            print(f"Saved merged test suite to: {self.llm_test_file}")
            print(f"Final test suite: {len(cleaned_tests)} characters")
            
            return True
            
        except Exception as e:
            print(f"Error saving merged tests: {e}")
            return False
    
    def _clean_llm_response(self, response):
        """Clean the LLM response to extract just the Python code."""
        # Remove markdown code blocks if present
        lines = response.split('\n')
        
        # Find start and end of Python code
        start_idx = 0
        end_idx = len(lines)
        
        for i, line in enumerate(lines):
            if line.strip().startswith('```python'):
                start_idx = i + 1
                break
            elif line.strip().startswith('import') or line.strip().startswith('# '):
                start_idx = i
                break
        
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() == '```':
                end_idx = i
                break
        
        # Extract the Python code
        python_code = '\n'.join(lines[start_idx:end_idx])
        
        return python_code.strip()
    
    def get_merged_test_path(self):
        """Get the path to the merged test file."""
        return str(self.llm_test_file)
    
    def run_tests(self):
        """Run the merged test suite to verify it works."""
        print("Running merged test suite...")
        
        import subprocess
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", str(self.llm_test_file), "-v"],
                cwd=project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("All tests passed!")
                print(result.stdout)
                return True
            else:
                print("Some tests failed:")
                print(result.stdout)
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"Error running tests: {e}")
            return False


def main():
    """Main function to run the test merger."""
    if len(sys.argv) < 2:
        print("Usage: python test_merger.py <source_file_name>")
        print("Example: python test_merger.py sample_calculator")
        return
    
    source_file_name = sys.argv[1]
    
    try:
        merger = TestSuiteMerger(source_file_name)
        
        print(f"Starting test suite merge for: {source_file_name}")
        
        if merger.merge_test_suites():
            print("Test suite merge completed successfully!")
            
            # Optionally run tests to verify they work
            run_tests = input("Run merged tests to verify? (y/n): ").lower().strip()
            if run_tests == 'y':
                merger.run_tests()
        else:
            print("Test suite merge failed!")
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
