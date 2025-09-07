"""
Format Extracted Information for Prompt for ASTER-style static analysis.
Prepares all extracted data in a format suitable for LLM prompt construction, matching the ASTER template.
"""

import os
from typing import Dict, Any, List, Optional
from typing_extensions import Format
from function_extractor import extract_top_level_functions
from class_extractor import extract_classes
from import_extractor import extract_imports
from monkeypatch_extractor import identify_monkeypatch_points


def format_module_analysis_for_prompt(
    functions: List[Dict[str, Any]],
    classes: List[Dict[str, Any]], 
    imports: Dict[str, Any],
    monkeypatch_points: Dict[str, Any],
    module_source: str,
    module_file_path: str = None,
    include_docstrings: bool = True,
    include_type_annotations: bool = True,
    include_source_in_prompt: bool = True
) -> Dict[str, str]:
    #Format all extracted module analysis information for ASTER-style LLM prompt.
    prompt_sections = {}
    
    # Section 1: Module Reference (save as file if path provided)
    prompt_sections['module_reference'] = _format_module_reference_section(
        module_source, module_file_path, include_source_in_prompt
    )
    
    # Section 2: Available Dependencies and Imports
    prompt_sections['dependencies_context'] = _format_dependencies_context_section(imports)
    
    # Section 3: Function Signatures and Details
    prompt_sections['function_signatures'] = _format_function_signatures_section(
        functions, include_docstrings, include_type_annotations
    )
    
    # Section 4: Class Definitions and Method Details
    prompt_sections['class_definitions'] = _format_class_definitions_section(
        classes, include_docstrings, include_type_annotations
    )
    
    # Section 5: External Dependencies and Mocking Strategy
    prompt_sections['mocking_strategy'] = _format_mocking_strategy_section(monkeypatch_points)
    
    # Section 6: Test Generation Guidelines
    prompt_sections['test_guidelines'] = _get_test_generation_guidelines()
    
    # Section 7: Test Targets Summary
    prompt_sections['test_targets'] = _format_test_targets_section(functions, classes)
    
    return prompt_sections


def _format_module_reference_section(module_source: str, module_file_path: str = None, include_source: bool = True) -> str:
    #Format the module source code section or create a file reference.
    if not include_source:
        # When file is uploaded separately, don't include source in prompt
        return "MODULE SOURCE CODE: [Provided as uploaded file]"
    
    if module_file_path:
        # Save module to file and reference it
        try:
            with open(module_file_path, 'w') as f:
                f.write(module_source)
            file_name = os.path.basename(module_file_path)
            return (
                f"MODULE SOURCE: Please refer to the attached file: {file_name}\n"
                f"IMPORTANT: When writing your test suite, use the following import statement as the FIRST line of your test file (replace 'test_file' with your actual test file name if needed):\n"
                f"    import {file_name.replace('.py', '')}\n"
                f"(The file name to import is: {file_name})"
            )
        except Exception:
            # Fallback to inline if file creation fails
            pass
    # Inline module source
    return f"MODULE SOURCE CODE:\n```python\n{module_source.strip()}\n```"


def _format_dependencies_context_section(imports: Dict[str, Any]) -> str:
    #Format the dependencies and imports context section.
    lines = ["AVAILABLE DEPENDENCIES AND IMPORTS:"]
    lines.append("The following dependencies are available for use in your test code:")
    lines.append("")
    
    if imports and imports.get('import_statements'):
        lines.append("Standard Library and Third-party Imports:")
        for stmt in imports['import_statements']:
            lines.append(f"  {stmt}")
        lines.append("")
    
    # Always include pytest imports
    lines.append("Testing Framework Imports (always available):")
    lines.append("  import pytest")
    lines.append("  from unittest.mock import Mock, patch, MagicMock")
    lines.append("")
    
    return '\n'.join(lines)


def _format_function_signatures_section(
    functions: List[Dict[str, Any]],
    include_docstrings: bool,
    include_type_annotations: bool
) -> str:
    #Format the function signatures section with detailed information.
    if not functions:
        return "FUNCTION SIGNATURES:\nNo functions found in the module."
    
    lines = ["FUNCTION SIGNATURES AND DETAILS:"]
    lines.append("The following functions are available and need comprehensive testing:")
    lines.append("")
    
    for func in functions:
        lines.append(f"Function: {func['name']}")
        lines.append(f"  Signature: {func['signature']}")
        
        # Parameter details
        if func.get('parameters'):
            lines.append("  Parameters:")
            for param in func['parameters']:
                param_line = f"    - {param['name']}"
                if param.get('type_annotation'):
                    param_line += f" (type: {param['type_annotation']})"
                if param.get('default_value'):
                    param_line += f" [default: {param['default_value']}]"
                if param.get('kind'):
                    param_line += f" [{param['kind']}]"
                lines.append(param_line)
        else:
            lines.append("  Parameters: None")
        
        # Return type
        if func.get('return_type'):
            lines.append(f"  Return Type: {func['return_type']}")
        else:
            lines.append("  Return Type: Not specified")
        
        # Docstring
        if include_docstrings and func.get('docstring'):
            lines.append(f"  Description: {func['docstring'].split('.')[0]}.")
        
        # Complexity hints
        if func.get('complexity_score'):
            lines.append(f"  Complexity: {func['complexity_score']}")
        
        lines.append("")
    
    return '\n'.join(lines)


def _format_class_definitions_section(
    classes: List[Dict[str, Any]],
    include_docstrings: bool,
    include_type_annotations: bool
) -> str:
    #Format the class definitions section with detailed method information.
    
    if not classes:
        return "CLASS DEFINITIONS:\nNo classes found in the module."
    
    lines = ["CLASS DEFINITIONS AND METHOD DETAILS:"]
    lines.append("The following classes are available and need comprehensive testing:")
    lines.append("")
    
    for cls in classes:
        lines.append(f"Class: {cls['name']}")
        lines.append(f"  Signature: {cls['signature']}")
        
        # Class docstring
        if include_docstrings and cls.get('docstring'):
            lines.append(f"  Description: {cls['docstring'].split('.')[0]}.")
        
        # Constructor details
        if cls.get('init_method'):
            init = cls['init_method']
            lines.append("  Constructor (__init__):")
            lines.append(f"    Signature: {init['signature']}")
            if init.get('parameters'):
                lines.append("    Parameters:")
                for param in init['parameters']:
                    param_line = f"      - {param['name']}"
                    if param.get('type_annotation'):
                        param_line += f" (type: {param['type_annotation']})"
                    if param.get('default_value'):
                        param_line += f" [default: {param['default_value']}]"
                    lines.append(param_line)
        
        # All methods (not limiting to 3)
        if cls.get('methods'):
            lines.append("  Methods:")
            for method in cls['methods']:
                lines.append(f"    Method: {method['name']}")
                lines.append(f"      Signature: {method['signature']}")
                
                if method.get('parameters'):
                    lines.append("      Parameters:")
                    for param in method['parameters']:
                        param_line = f"        - {param['name']}"
                        if param.get('type_annotation'):
                            param_line += f" (type: {param['type_annotation']})"
                        if param.get('default_value'):
                            param_line += f" [default: {param['default_value']}]"
                        lines.append(param_line)
                
                if method.get('return_type'):
                    lines.append(f"      Return Type: {method['return_type']}")
                
                if include_docstrings and method.get('docstring'):
                    lines.append(f"      Description: {method['docstring'].split('.')[0]}.")
                
                lines.append("")
        
        lines.append("")
    
    return '\n'.join(lines)


def _format_mocking_strategy_section(monkeypatch_points: Dict[str, Any]) -> str:
    #Format the mocking strategy section with correct pytest monkeypatch usage.
    lines = ["EXTERNAL DEPENDENCIES AND MOCKING STRATEGY:"]
    
    if not monkeypatch_points.get('all_monkeypatch_targets'):
        lines.append("No external dependencies requiring mocking were detected.")
        lines.append("You can focus on testing the core logic without mocking concerns.")
        return '\n'.join(lines)
    
    lines.append("The following external dependencies were detected and should be mocked in tests:")
    lines.append("")
    
    targets = monkeypatch_points['all_monkeypatch_targets']
    
    # List all detected targets
    lines.append("Detected External Calls:")
    for target in targets:
        lines.append(f"  - {target}")
    lines.append("")
    
    # Correct monkeypatch examples by category
    lines.append("CORRECT MOCKING EXAMPLES:")
    lines.append("Use pytest's monkeypatch fixture with the following patterns:")
    lines.append("")
    
    # Network operations
    if monkeypatch_points.get('network_operations'):
        lines.append("Network Operations Mocking:")
        for call_info in monkeypatch_points['network_operations']:
            target = call_info['full_call']
            if 'requests.' in target:
                lines.append(f"  import requests")
                lines.append(f"  monkeypatch.setattr(requests, '{target.split('.')[-1]}', lambda *args, **kwargs: mock_response)")
            elif target == 'urllib.request.urlopen':
                lines.append(f"  import urllib.request")
                lines.append(f"  monkeypatch.setattr(urllib.request, 'urlopen', lambda *args, **kwargs: mock_response)")
            else:
                module_path = '.'.join(target.split('.')[:-1])
                attr_name = target.split('.')[-1]
                lines.append(f"  import {module_path}")
                lines.append(f"  monkeypatch.setattr({module_path}, '{attr_name}', lambda *args, **kwargs: mock_response)")
        lines.append("")
    
    # File operations
    if monkeypatch_points.get('file_operations'):
        lines.append("File Operations Mocking:")
        for call_info in monkeypatch_points['file_operations']:
            target = call_info['full_call']
            if target == 'open':
                lines.append("  monkeypatch.setattr('builtins.open', mock_open_function)")
            elif 'os.' in target:
                lines.append(f"  import os")
                lines.append(f"  monkeypatch.setattr(os, '{target.split('.')[-1]}', lambda *args, **kwargs: mock_result)")
            else:
                lines.append(f"  monkeypatch.setattr('{target}', lambda *args, **kwargs: mock_result)")
        lines.append("")
    
    # Other external calls
    other_targets = [target for target in targets 
                    if not any(target in [ci['full_call'] for ci in cat] 
                             for cat in [monkeypatch_points.get('network_operations', []),
                                       monkeypatch_points.get('file_operations', [])])]
    
    if other_targets:
        lines.append("Other External Dependencies:")
        for target in other_targets:
            if '.' in target:
                module_path = '.'.join(target.split('.')[:-1])
                attr_name = target.split('.')[-1]
                lines.append(f"  import {module_path}")
                lines.append(f"  monkeypatch.setattr({module_path}, '{attr_name}', lambda *args, **kwargs: mock_result)")
            else:
                lines.append(f"  monkeypatch.setattr('builtins.{target}', lambda *args, **kwargs: mock_result)")
        lines.append("")
    
    # General mocking guidelines
    lines.append("MOCKING GUIDELINES:")
    lines.append("- Use descriptive mock return values that match expected data types")
    lines.append("- Create separate test functions for different mock scenarios")
    lines.append("- Test both success and failure cases by varying mock return values")
    lines.append("- Use pytest fixtures for complex mock setups")
    lines.append("")
    
    return '\n'.join(lines)


def _get_test_generation_guidelines() -> str:
    #Get comprehensive test generation guidelines for the LLM.
    return """TEST GENERATION GUIDELINES AND REQUIREMENTS:

TESTING FRAMEWORK:
- Use pytest framework exclusively
- Follow pytest best practices and conventions
- Use descriptive test function names that explain what is being tested

TEST STRUCTURE:
- Follow the Arrange-Act-Assert (AAA) pattern
- Use clear variable names and comments
- Group related tests using pytest classes when appropriate

COVERAGE REQUIREMENTS:
- Test all public functions and class methods with STRATEGIC coverage, not exhaustive repetition
- Include positive test cases (expected behavior) - focus on representative examples, not all variations
- Include negative test cases (error conditions) - prioritize unique error scenarios
- Test edge cases and boundary conditions - select the most critical boundaries
- Test with different input types where applicable - use minimal but comprehensive type coverage
- PRIORITIZE test cases that reveal different code paths and logical branches
- AVOID testing multiple variations of the same underlying logic unless they exercise different code paths

ERROR HANDLING:
- Test exception raising using pytest.raises()
- Verify proper error messages and types
- Test error conditions and invalid inputs

DATA TYPES AND VALIDATION:
- Test with various data types (if function accepts multiple types)
- Test with None values where applicable
- Test with empty collections (lists, dicts, strings)
- Test with large inputs if relevant

PARAMETRIZED TESTING:
- Use @pytest.mark.parametrize for testing multiple input combinations STRATEGICALLY
- Create data-driven tests for comprehensive coverage WITHOUT redundancy
- Limit parametrized test cases to 3-5 representative scenarios per test function
- Group similar test scenarios into focused, concise parametrized tests
- AVOID creating massive parameter lists that test trivial variations of the same logic

FIXTURE USAGE:
- Use pytest fixtures for setup and teardown
- Create reusable test data with fixtures
- Use monkeypatch fixture for mocking external dependencies

TEST QUALITY:
- Write self-documenting tests with clear assertions
- Include docstrings for complex test scenarios
- Ensure tests are independent and can run in any order
- Make tests fast and reliable
- AVOID REDUNDANT TEST CASES: Do not create multiple test functions that test the same scenario or functionality
- Focus on unique test scenarios that add distinct value to the test suite
- Consolidate similar test cases using parametrized testing instead of creating separate functions
- EFFICIENCY OVER QUANTITY: Prefer fewer, well-designed tests that provide maximum coverage and value
- Each test should target a specific behavior, edge case, or error condition - avoid testing trivial variations
- Limit parametrized tests to 3-5 meaningful scenarios that exercise different code paths or logic branches

TEST DESIGN PRINCIPLES:
- SELECT REPRESENTATIVE EXAMPLES: Choose test cases that represent broader categories of input
- FOCUS ON BOUNDARIES: Test edge cases like zero, negative numbers, empty inputs, maximum values
- TARGET ERROR CONDITIONS: Test each unique error path (division by zero, invalid types, etc.)
- MINIMIZE REPETITION: If two test cases exercise the same code path with similar logic, combine or eliminate one
- MAXIMIZE VALUE: Each test case should either verify different functionality or expose different potential failures
"""


def _format_test_targets_section(functions: List[Dict[str, Any]], classes: List[Dict[str, Any]]) -> str:
    #Format the test targets section with complete coverage requirements.

    lines = ["TEST TARGETS SUMMARY:"]
    lines.append("You must generate comprehensive tests for ALL of the following:")
    lines.append("")
    
    if functions:
        lines.append("FUNCTIONS TO TEST:")
        for func in functions:
            param_details = []
            for param in func.get('parameters', []):
                param_str = param['name']
                if param.get('type_annotation'):
                    param_str += f": {param['type_annotation']}"
                if param.get('default_value'):
                    param_str += f" = {param['default_value']}"
                param_details.append(param_str)
            
            param_list = ', '.join(param_details) if param_details else ""
            return_info = f" -> {func['return_type']}" if func.get('return_type') else ""
            
            lines.append(f"  ✓ {func['name']}({param_list}){return_info}")
            if func.get('docstring'):
                lines.append(f"    Purpose: {func['docstring'].split('.')[0]}.")
        lines.append("")
    
    if classes:
        lines.append("CLASSES TO TEST:")
        for cls in classes:
            lines.append(f"  ✓ Class: {cls['name']}")
            
            if cls.get('init_method'):
                init = cls['init_method']
                init_params = []
                for param in init.get('parameters', []):
                    param_str = param['name']
                    if param.get('type_annotation'):
                        param_str += f": {param['type_annotation']}"
                    if param.get('default_value'):
                        param_str += f" = {param['default_value']}"
                    init_params.append(param_str)
                
                param_list = ', '.join(init_params) if init_params else ""
                lines.append(f"    ✓ Constructor: __init__({param_list})")
            
            # Include ALL methods
            for method in cls.get('methods', []):
                method_params = []
                for param in method.get('parameters', []):
                    param_str = param['name']
                    if param.get('type_annotation'):
                        param_str += f": {param['type_annotation']}"
                    if param.get('default_value'):
                        param_str += f" = {param['default_value']}"
                    method_params.append(param_str)
                
                param_list = ', '.join(method_params) if method_params else ""
                return_info = f" -> {method['return_type']}" if method.get('return_type') else ""
                
                lines.append(f"    ✓ Method: {method['name']}({param_list}){return_info}")
                if method.get('docstring'):
                    lines.append(f"      Purpose: {method['docstring'].split('.')[0]}.")
            lines.append("")
    
    if not functions and not classes:
        lines.append("No testable functions or classes found in the module.")
    
    lines.append("DELIVERABLES:")
    lines.append("Generate a complete test suite that covers all the above targets with:")
    lines.append("- Comprehensive test coverage for each function and method")
    lines.append("- Edge cases and error condition testing")
    lines.append("- Proper mocking of external dependencies")
    lines.append("- Clear, maintainable, and well-documented test code")
    
    return '\n'.join(lines)




def create_full_aster_prompt(
    module_source: str,
    functions: List[Dict[str, Any]],
    classes: List[Dict[str, Any]], 
    imports: Dict[str, Any],
    monkeypatch_points: Dict[str, Any],
    module_file_path: str = None,
    module_name: str = None,
    include_docstrings: bool = True,
    include_type_annotations: bool = True,
    include_source_in_prompt: bool = True
) -> str:
    #Create a complete ASTER-style prompt from all extracted information.
    # Format all sections
    sections = format_module_analysis_for_prompt(
        functions, classes, imports, monkeypatch_points, module_source,
        module_file_path, include_docstrings, include_type_annotations, include_source_in_prompt
    )
    
    # Assemble the final prompt with clear structure and no hashtags
    prompt_parts = []
    
    # Header
    prompt_parts.append("=" * 80)
    prompt_parts.append("COMPREHENSIVE UNIT TEST GENERATION REQUEST")
    prompt_parts.append("=" * 80)
    prompt_parts.append("")
    
    # Section 1: Module Reference
    prompt_parts.append("SECTION 1: " + "=" * 68)
    prompt_parts.append(sections['module_reference'])
    prompt_parts.append("")
    
    # Section 2: Dependencies Context
    prompt_parts.append("SECTION 2: " + "=" * 68)
    prompt_parts.append(sections['dependencies_context'])
    
    # Section 3: Function Analysis
    prompt_parts.append("SECTION 3: " + "=" * 68)
    prompt_parts.append(sections['function_signatures'])
    
    # Section 4: Class Analysis
    prompt_parts.append("SECTION 4: " + "=" * 68)
    prompt_parts.append(sections['class_definitions'])
    
    # Section 5: Mocking Strategy
    prompt_parts.append("SECTION 5: " + "=" * 68)
    prompt_parts.append(sections['mocking_strategy'])
    
    # Section 6: Guidelines
    prompt_parts.append("SECTION 6: " + "=" * 68)
    prompt_parts.append(sections['test_guidelines'])
    
    # Section 7: Test Targets
    prompt_parts.append("SECTION 7: " + "=" * 68)
    prompt_parts.append(sections['test_targets'])
    
    # Final Instructions
    prompt_parts.append("")
    prompt_parts.append("=" * 80)
    prompt_parts.append("FINAL INSTRUCTIONS:")
    prompt_parts.append("=" * 80)
    prompt_parts.append("")
    prompt_parts.append("Please generate a complete, comprehensive pytest test suite that:")
    prompt_parts.append("")
    prompt_parts.append("1. COVERAGE: Tests every function and method listed in the test targets")
    prompt_parts.append("2. QUALITY: Follows all the testing guidelines provided above")
    prompt_parts.append("3. COMPLETENESS: Includes positive, negative, and edge case scenarios")
    prompt_parts.append("4. MOCKING: Properly mocks all external dependencies as specified")
    prompt_parts.append("5. STRUCTURE: Uses clear test organization and descriptive names")
    prompt_parts.append("6. DOCUMENTATION: Includes docstrings for complex test scenarios")
    prompt_parts.append("7. EFFICIENCY: Minimizes redundancy while maximizing meaningful coverage")
    prompt_parts.append("8. FOCUS: Each test should target distinct functionality or reveal different potential issues")
    prompt_parts.append("")
    prompt_parts.append("CRITICAL REQUIREMENTS:")
    prompt_parts.append("- Limit parametrized tests to 3-5 representative cases that exercise different logic paths")
    prompt_parts.append("- Avoid creating multiple variations of the same basic functionality test")
    prompt_parts.append("- Focus on boundary conditions, error paths, and unique behavioral scenarios")
    prompt_parts.append("- Prefer strategic test design over exhaustive input permutation testing")
    prompt_parts.append("")
    # Insert the actual file name for the import statement in the instructions
    if module_file_path:
        file_name = os.path.basename(module_file_path)
        import_stmt = f"import {file_name.replace('.py', '')}"
        prompt_parts.append(f"IMPORTANT: The FIRST line of your test file must be: ../source/{import_stmt}")
        prompt_parts.append(f"Do NOT use any other import path or name. Use exactly: ../source/{import_stmt}")
    elif module_name:
        import_stmt = f"import {module_name}"
        prompt_parts.append(f"IMPORTANT: The FIRST line of your test file must be: ../source/{import_stmt}")
        prompt_parts.append(f"Do NOT use any other import path or name. Use exactly: ../source/{import_stmt}")
    else:
        prompt_parts.append("IMPORTANT: The FIRST line of your test file must be an import statement for the module under test, using the exact file name provided above. Do NOT use any other import path or name.")
    prompt_parts.append("")
    prompt_parts.append("The generated test suite should be production-ready and provide")
    prompt_parts.append("comprehensive coverage of the module under test.")
    prompt_parts.append("")
    prompt_parts.append("=" * 80)
    
    return '\n'.join(prompt_parts)
