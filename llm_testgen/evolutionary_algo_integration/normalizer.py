"""Enhanced normalization pipeline for preparing LLM generated tests as Pynguin seeds.

This module exposes a function `generate_seed_file` and a CLI.
Key features:
  - Collects raw test files (pattern: test_*.py) excluding already normalized *_seed.py.
  - Extracts calls to target functions (supports attribute or direct reference).
  - Expands parametrized tests into individual seed cases with dynamic parameter mapping.
  - Resolves variable assignments within test functions to extract literal values.
  - Handles complex expressions including collections (lists, tuples, dicts) and arithmetic.
  - Groups each call into an individual `test_seed_<n>()` function.
  - Writes a single consolidated seed file next to the originals with suffix `_seed.py`.
  - Idempotent: rewrites only if content changes (SHA256 hash comparison).
  - Safe: never overwrites non-seed files.
  - Generic: works with any Python function signature and test structure.

Design constraints (Pynguin parser limitations):
  - Arguments must be variable names bound to supported types.
  - No fixtures, parametrization, context managers, or complex expressions in final output.
  - One call per generated seed test to keep statements simple and evolvable.

Supported Types:
  - Primitives: int, float, str, bool, None
  - Collections: list, tuple, dict (with nested support)
  - Safe evaluation of arithmetic and unary operations

Usage:
  python -m evolutionary_algo_integration.normalizer \
      --tests-dir tests/test_suites \
      --module-name sample_calculator \
      --function-name calculator

Result:
  tests/test_suites/test_sample_calculator_seed.py (example)
"""
from __future__ import annotations

import ast
import argparse
import hashlib
import operator
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Dict, Any, Union, Optional, Tuple

# Supported literal types for Pynguin compatibility
ALLOWED_LITERAL_TYPES = (int, float, str, bool, type(None), complex, bytes, bytearray)
ALLOWED_COLLECTION_TYPES = (list, tuple, dict, set, frozenset)
ALLOWED_TYPES = ALLOWED_LITERAL_TYPES + ALLOWED_COLLECTION_TYPES

# Operator mapping for safe evaluation
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

@dataclass
class CallContext:
    """Context information for a function call within a test."""
    call: ast.Call
    local_vars: Dict[str, Any]
    test_name: str
    function_name: str  # Add function name to context


@dataclass
class ExtractionConfig:
    """Configuration for test extraction and seed generation."""
    module_name: str
    function_names: List[str]  # Changed to support multiple functions
    tests_dir: Path
    auto_discover: bool = True  # Automatically discover functions from source module


@dataclass
class ParametrizedTestInfo:
    """Information about a parametrized test."""
    function_def: ast.FunctionDef
    parameter_names: List[str]
    parameter_sets: List[List[Any]]
    class_name: Optional[str] = None


def _discover_functions_from_source(source_file_path: Path) -> List[str]:
    """Discover all functions and classes from the source module."""
    if not source_file_path.exists():
        return []
    
    try:
        tree = ast.parse(source_file_path.read_text(encoding="utf-8"))
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Include all functions except private ones and dunder methods
                if not node.name.startswith('_'):
                    functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                # Include class names for potential static/class methods
                if not node.name.startswith('_'):
                    functions.append(node.name)
                    # Also add methods from the class
                    for class_node in node.body:
                        if isinstance(class_node, ast.FunctionDef) and not class_node.name.startswith('_'):
                            functions.append(class_node.name)
        
        return list(set(functions))  # Remove duplicates
    except Exception:
        return []


def _discover_test_function_targets(test_file_path: Path) -> List[str]:
    """Discover function names being tested by analyzing function calls in test files."""
    if not test_file_path.exists():
        return []
    
    try:
        tree = ast.parse(test_file_path.read_text(encoding="utf-8"))
        called_functions = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Direct function calls: func_name()
                if isinstance(node.func, ast.Name):
                    called_functions.add(node.func.id)
                # Attribute calls: module.func_name() or obj.method()
                elif isinstance(node.func, ast.Attribute):
                    called_functions.add(node.func.attr)
                    # Also check if it's a module call pattern like sample_calculator_flask.calculator
                    if isinstance(node.func.value, ast.Name):
                        # This is for calls like module_name.function_name
                        called_functions.add(node.func.attr)
        
        # Filter to likely function names (exclude common test utilities and built-ins)
        excluded_names = {
            'get', 'post', 'put', 'delete', 'patch', 'head', 'options',  # HTTP methods
            'assert', 'assertEqual', 'assertTrue', 'assertFalse', 'assertRaises',  # Test assertions
            'setUp', 'tearDown', 'fixture', 'mock', 'patch', 'Mock', 'MagicMock',  # Test utilities
            'config', 'testing', 'test_client', 'test_request_context',  # Flask test utilities
            'get_json', 'status_code', 'json', 'data', 'headers',  # Response utilities
            'insert', 'append', 'add', 'remove', 'clear', 'pop',  # Collection methods
            'str', 'int', 'float', 'bool', 'list', 'dict', 'set', 'tuple',  # Built-in types
            'len', 'range', 'enumerate', 'zip', 'map', 'filter', 'any', 'all',  # Built-in functions
            'Path', 'pathlib', 'os', 'sys', 'math', 'json', 'time',  # Common modules
            'read_text', 'write_text', 'exists', 'is_file', 'is_dir',  # Path methods
        }
        
        return list(called_functions - excluded_names)
    except Exception:
        return []


def _iter_raw_test_files(tests_dir: Path) -> Iterable[Path]:
    """Iterate over raw test files, excluding already normalized seed files."""
    for path in tests_dir.glob("llm_generated_test_*.py"):
        if path.name.endswith("_seed.py"):
            continue
        if path.is_file():
            yield path


def _is_valid_argument_type(value: Any) -> bool:
    """Check if a value is of a type supported by Pynguin."""
    if isinstance(value, ALLOWED_LITERAL_TYPES):
        return True
    elif isinstance(value, ALLOWED_COLLECTION_TYPES):
        return _is_valid_collection_type(value)
    return False


def _is_valid_collection_type(value: Any) -> bool:
    """Recursively validate collection types and their contents."""
    if isinstance(value, (list, tuple)):
        return all(_is_valid_argument_type(item) for item in value)
    elif isinstance(value, dict):
        # Only allow string keys for safety
        return (all(isinstance(k, str) for k in value.keys()) and
                all(_is_valid_argument_type(v) for v in value.values()))
    elif isinstance(value, (set, frozenset)):
        return all(_is_valid_argument_type(item) for item in value)
    return False


def _safe_eval_literal(node: ast.AST) -> Any:
    """Safely evaluate an AST node to extract literal values and collections.
    
    Supports:
    - Constants (int, float, str, bool, None)
    - Arithmetic operations (+, -, *, /, **, %)
    - Unary operations (+x, -x)
    - Collections (list, tuple, dict) with recursive evaluation
    
    Args:
        node: AST node to evaluate
        
    Returns:
        Evaluated value
        
    Raises:
        ValueError: If the node cannot be safely evaluated
    """
    if isinstance(node, ast.Constant):
        return node.value
    
    elif isinstance(node, ast.UnaryOp):
        operand = _safe_eval_literal(node.operand)
        op_func = SAFE_OPERATORS.get(type(node.op))
        if op_func:
            return op_func(operand)
        raise ValueError(f"Unsupported unary operator: {type(node.op)}")
    
    elif isinstance(node, ast.BinOp):
        left = _safe_eval_literal(node.left)
        right = _safe_eval_literal(node.right)
        op_func = SAFE_OPERATORS.get(type(node.op))
        if op_func:
            return op_func(left, right)
        raise ValueError(f"Unsupported binary operator: {type(node.op)}")
    
    elif isinstance(node, ast.List):
        return [_safe_eval_literal(elt) for elt in node.elts]
    
    elif isinstance(node, ast.Tuple):
        return tuple(_safe_eval_literal(elt) for elt in node.elts)
    
    elif isinstance(node, ast.Dict):
        result = {}
        for key_node, value_node in zip(node.keys, node.values):
            if key_node is None:  # **kwargs expansion
                raise ValueError("Dictionary unpacking not supported")
            key = _safe_eval_literal(key_node)
            if not isinstance(key, str):
                raise ValueError("Only string keys supported for dictionaries")
            value = _safe_eval_literal(value_node)
            result[key] = value
        return result
    
    elif isinstance(node, ast.Set):
        return {_safe_eval_literal(elt) for elt in node.elts}
    
    elif isinstance(node, ast.Call):
        # Handle specific function calls like complex(), bytes(), set(), etc.
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            
            if func_name == 'complex' and len(node.args) >= 1:
                if len(node.args) == 1:
                    real = _safe_eval_literal(node.args[0])
                    return complex(real)
                elif len(node.args) == 2:
                    real = _safe_eval_literal(node.args[0])
                    imag = _safe_eval_literal(node.args[1])
                    return complex(real, imag)
            
            elif func_name == 'bytes' and len(node.args) >= 1:
                if len(node.args) == 1:
                    arg = _safe_eval_literal(node.args[0])
                    if isinstance(arg, str):
                        return arg.encode('utf-8')
                    elif isinstance(arg, (list, tuple)):
                        return bytes(arg)
                
            elif func_name == 'set':
                if len(node.args) == 0:
                    return set()
                elif len(node.args) == 1:
                    arg = _safe_eval_literal(node.args[0])
                    if isinstance(arg, (list, tuple)):
                        return set(arg)
                        
            elif func_name == 'frozenset':
                if len(node.args) == 0:
                    return frozenset()
                elif len(node.args) == 1:
                    arg = _safe_eval_literal(node.args[0])
                    if isinstance(arg, (list, tuple, set)):
                        return frozenset(arg)
    
    raise ValueError(f"Cannot safely evaluate: {ast.dump(node)}")


def _is_pytest_parametrize(decorator: ast.expr) -> bool:
    """Check if a decorator is pytest.mark.parametrize."""
    if not isinstance(decorator, ast.Call):
        return False
    
    func = decorator.func
    if isinstance(func, ast.Attribute):
        if isinstance(func.value, ast.Attribute):
            return (isinstance(func.value.value, ast.Name) and 
                    func.value.value.id == "pytest" and 
                    func.value.attr == "mark" and 
                    func.attr == "parametrize")
    return False


def _extract_parameter_names(param_names_node: ast.expr) -> List[str]:
    """Extract parameter names from pytest.mark.parametrize first argument.
    
    Handles both single string ('x') and comma-separated string ('a, b, c').
    """
    if isinstance(param_names_node, ast.Constant) and isinstance(param_names_node.value, str):
        names = param_names_node.value.split(',')
        return [name.strip() for name in names]
    return []


def _extract_parameter_values(param_values_node: ast.expr) -> List[List[Any]]:
    """Extract parameter value sets from pytest.mark.parametrize second argument."""
    if isinstance(param_values_node, ast.List):
        result = []
        for item in param_values_node.elts:
            try:
                if isinstance(item, ast.Tuple):
                    # Multiple parameters: (val1, val2, val3)
                    values = [_safe_eval_literal(elt) for elt in item.elts]
                    result.append(values)
                else:
                    # Single parameter: val
                    value = _safe_eval_literal(item)
                    result.append([value])
            except ValueError:
                # Skip invalid parameter sets
                continue
        return result
    return []


def _extract_parametrized_data(decorator: ast.expr) -> Tuple[List[str], List[List[Any]]]:
    """Extract parameter names and value sets from pytest.mark.parametrize decorator.
    
    Returns:
        Tuple of (parameter_names, parameter_sets)
    """
    if not _is_pytest_parametrize(decorator):
        return [], []
    
    if len(decorator.args) >= 2:
        param_names = _extract_parameter_names(decorator.args[0])
        param_values = _extract_parameter_values(decorator.args[1])
        return param_names, param_values
    
    return [], []


def _collect_local_variables(func_def: ast.FunctionDef) -> Dict[str, Any]:
    """Collect variable assignments from a function definition.
    
    Args:
        func_def: Function definition AST node
        
    Returns:
        Dictionary mapping variable names to their values
    """
    local_vars = {}
    
    for node in ast.walk(func_def):
        if isinstance(node, ast.Assign):
            # Skip known problematic variable names (Mock, monkeypatch, etc.)
            if any(isinstance(target, ast.Name) and target.id.lower() in ('mock', 'monkeypatch', 'mock_print', 'result')
                   for target in node.targets if isinstance(target, ast.Name)):
                continue
            
            # Handle single assignment: var = value
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                var_name = node.targets[0].id
                try:
                    value = _safe_eval_literal(node.value)
                    if _is_valid_argument_type(value):
                        local_vars[var_name] = value
                except ValueError:
                    # Skip complex expressions that can't be evaluated
                    continue
            
            # Handle tuple unpacking: a, b = 10, 5
            elif len(node.targets) == 1 and isinstance(node.targets[0], ast.Tuple):
                try:
                    values = _safe_eval_literal(node.value)
                    if isinstance(values, (list, tuple)) and len(values) == len(node.targets[0].elts):
                        for target_elt, value in zip(node.targets[0].elts, values):
                            if isinstance(target_elt, ast.Name):
                                var_name = target_elt.id
                                if _is_valid_argument_type(value):
                                    local_vars[var_name] = value
                except ValueError:
                    # Skip complex expressions
                    continue
    
    return local_vars


def _is_target_call(call_node: ast.Call, target_func: str) -> bool:
    """Check if a call node targets the specified function."""
    func = call_node.func
    if isinstance(func, ast.Name):
        return func.id == target_func
    elif isinstance(func, ast.Attribute):
        # Handle both direct attribute calls and module.function calls
        if func.attr == target_func:
            return True
        # Special handling for Flask test client calls that may indirectly test API functions
        if target_func == "calculate_api" and func.attr == "get":
            # Check if this is a client.get call to '/calculate' endpoint
            if (len(call_node.args) > 0 and 
                isinstance(call_node.args[0], ast.Constant) and 
                isinstance(call_node.args[0].value, str) and 
                call_node.args[0].value.startswith('/calculate')):
                return True
    return False


def _find_target_calls(func_def: ast.FunctionDef, target_func: str) -> List[ast.Call]:
    """Find all calls to the target function within a function definition."""
    calls = []
    
    class CallVisitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call):
            if _is_target_call(node, target_func):
                calls.append(node)
            self.generic_visit(node)
    
    CallVisitor().visit(func_def)
    return calls


def _extract_calls_from_function(func_def: ast.FunctionDef, target_func: str) -> List[CallContext]:
    """Extract function calls and their contexts from a test function.
    
    Args:
        func_def: Function definition AST node
        target_func: Name of the target function to extract calls for
        
    Returns:
        List of CallContext objects
    """
    local_vars = _collect_local_variables(func_def)
    target_calls = _find_target_calls(func_def, target_func)
    
    return [CallContext(
        call=call,
        local_vars=local_vars.copy(),
        test_name=func_def.name,
        function_name=target_func
    ) for call in target_calls]


def _resolve_parametrized_assignments(func_def: ast.FunctionDef, param_mapping: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve assignments in a function that depend on parametrized values.
    
    Args:
        func_def: Function definition AST node
        param_mapping: Mapping of parameter names to values
        
    Returns:
        Dictionary of resolved variable assignments
    """
    resolved_vars = param_mapping.copy()
    
    # Process assignments in the function body
    for node in ast.walk(func_def):
        if isinstance(node, ast.Assign):
            # Handle single assignment: var = value
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                var_name = node.targets[0].id
                
                # Skip if already resolved or if it's a problematic variable
                if var_name in resolved_vars or var_name.lower() in ('mock', 'monkeypatch', 'mock_print', 'result'):
                    continue
                
                try:
                    # Try to resolve the value using the current parameter mapping
                    value = _resolve_expression_with_params(node.value, resolved_vars)
                    if value is not _UNRESOLVED and _is_valid_argument_type(value):
                        resolved_vars[var_name] = value
                except:
                    # Skip problematic assignments
                    continue
    
    return resolved_vars


def _resolve_expression_with_params(expr: ast.expr, param_mapping: Dict[str, Any]) -> Any:
    """Resolve an expression using parameter values.
    
    Args:
        expr: AST expression to resolve
        param_mapping: Mapping of parameter names to values
        
    Returns:
        Resolved value or _UNRESOLVED if cannot be resolved
    """
    if isinstance(expr, ast.Name):
        # Variable reference - look up in parameter mapping
        return param_mapping.get(expr.id, _UNRESOLVED)
    
    elif isinstance(expr, ast.List):
        # List literal - resolve each element
        resolved_elts = []
        for elt in expr.elts:
            elt_value = _resolve_expression_with_params(elt, param_mapping)
            if elt_value is _UNRESOLVED:
                return _UNRESOLVED
            resolved_elts.append(elt_value)
        return resolved_elts
    
    elif isinstance(expr, ast.Tuple):
        # Tuple literal - resolve each element
        resolved_elts = []
        for elt in expr.elts:
            elt_value = _resolve_expression_with_params(elt, param_mapping)
            if elt_value is _UNRESOLVED:
                return _UNRESOLVED
            resolved_elts.append(elt_value)
        return tuple(resolved_elts)
    
    else:
        # Try to evaluate as literal
        try:
            return _safe_eval_literal(expr)
        except ValueError:
            return _UNRESOLVED


def _generate_parametrized_calls(
    func_def: ast.FunctionDef,
    base_calls: List[CallContext], 
    param_names: List[str], 
    param_sets: List[List[Any]],
    class_name: Optional[str] = None
) -> List[CallContext]:
    """Generate call contexts for parametrized test cases.
    
    Args:
        func_def: Function definition containing the assignments
        base_calls: Base call contexts from the test function
        param_names: Parameter names from the parametrize decorator
        param_sets: Parameter value sets
        class_name: Optional class name for method tests
        
    Returns:
        List of CallContext objects with parameter values injected
    """
    parametrized_calls = []
    
    for i, param_set in enumerate(param_sets):
        for call_ctx in base_calls:
            # Create parameter mapping
            param_mapping = {}
            if len(param_names) == len(param_set):
                param_mapping = dict(zip(param_names, param_set))
            
            # Resolve assignments that depend on parameters
            resolved_vars = _resolve_parametrized_assignments(func_def, param_mapping)
            
            # Generate unique test name
            base_name = call_ctx.test_name
            if class_name:
                test_name = f"{class_name}_{base_name}_param_{i}"
            else:
                test_name = f"{base_name}_param_{i}"
            
            # Create new context with resolved parameter values and assignments
            new_ctx = CallContext(
                call=call_ctx.call,
                local_vars={**call_ctx.local_vars, **resolved_vars},
                test_name=test_name,
                function_name=call_ctx.function_name
            )
            parametrized_calls.append(new_ctx)
    
    return parametrized_calls


def _process_test_function(
    func_def: ast.FunctionDef, 
    target_func: str,
    class_name: Optional[str] = None
) -> List[CallContext]:
    """Process a single test function to extract calls.
    
    Args:
        func_def: Function definition AST node
        target_func: Name of the target function to extract calls for
        class_name: Optional class name for method tests
        
    Returns:
        List of CallContext objects
    """
    # Extract base calls from function body
    base_calls = _extract_calls_from_function(func_def, target_func)
    if not base_calls:
        return []
    
    # Check for parametrized decorators
    all_param_names = []
    all_param_sets = []
    
    for decorator in func_def.decorator_list:
        param_names, param_sets = _extract_parametrized_data(decorator)
        if param_names and param_sets:
            all_param_names = param_names
            all_param_sets.extend(param_sets)
    
    if all_param_sets:
        # Generate parametrized calls
        return _generate_parametrized_calls(func_def, base_calls, all_param_names, all_param_sets, class_name)
    else:
        # No parametrization, use direct calls
        if class_name:
            for call_ctx in base_calls:
                call_ctx.test_name = f"{class_name}_{call_ctx.test_name}"
        return base_calls


def _process_test_class(class_def: ast.ClassDef, target_func: str) -> List[CallContext]:
    """Process a test class to extract calls from all test methods.
    
    Args:
        class_def: Class definition AST node
        target_func: Name of the target function to extract calls for
        
    Returns:
        List of CallContext objects from all test methods
    """
    all_calls = []
    
    for node in class_def.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
            calls = _process_test_function(node, target_func, class_def.name)
            all_calls.extend(calls)
    
    return all_calls


def _extract_calls(tree: ast.AST, func_name: str) -> List[CallContext]:
    """Extract function calls from all test functions and classes in an AST.
    
    Processes both top-level test functions and test methods in classes.
    Handles parametrized tests by expanding them into individual cases.
    
    Args:
        tree: AST tree to process
        func_name: Name of the target function to extract calls for
        
    Returns:
        List of CallContext objects from all processed tests
    """
    all_calls = []
    processed_functions = set()  # Track processed functions to avoid duplicates
    
    # Process top-level nodes
    for node in tree.body if hasattr(tree, 'body') else []:
        if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
            # Process top-level test functions
            if node.name not in processed_functions:
                processed_functions.add(node.name)
                calls = _process_test_function(node, func_name)
                all_calls.extend(calls)
        
        elif isinstance(node, ast.ClassDef):
            # Process test classes
            calls = _process_test_class(node, func_name)
            all_calls.extend(calls)
    
    return all_calls


# Sentinel value to distinguish between "resolved to None" and "failed to resolve"
_UNRESOLVED = object()


def _resolve_argument_value(arg_node: ast.expr, local_vars: Dict[str, Any]) -> Any:
    """Resolve an argument node to its value using local variable context.
    
    Args:
        arg_node: AST node representing the argument
        local_vars: Local variable context
        
    Returns:
        Resolved value or _UNRESOLVED if cannot be resolved
    """
    if isinstance(arg_node, ast.Name):
        # Variable reference - look up in local context
        if arg_node.id in local_vars:
            return local_vars[arg_node.id]
        else:
            return _UNRESOLVED
    else:
        # Try to evaluate directly
        try:
            value = _safe_eval_literal(arg_node)
            return value if _is_valid_argument_type(value) else _UNRESOLVED
        except ValueError:
            return _UNRESOLVED


def _resolve_call_arguments(call_ctx: CallContext) -> Optional[Tuple[List[str], List[str]]]:
    """Resolve call arguments using local variable context.
    
    Args:
        call_ctx: Call context containing call and local variables
        
    Returns:
        Tuple of (setup_lines, argument_references) or None if resolution fails
    """
    setup: List[str] = []
    arg_refs: List[str] = []
    
    # Special handling for Flask test client calls
    if (call_ctx.function_name == "calculate_api" and 
        isinstance(call_ctx.call.func, ast.Attribute) and 
        call_ctx.call.func.attr == "get"):
        
        # This is a client.get() call testing the API endpoint
        # Extract URL parameters and convert to direct function call
        if (len(call_ctx.call.args) > 0 and 
            isinstance(call_ctx.call.args[0], ast.Constant) and 
            isinstance(call_ctx.call.args[0].value, str)):
            
            url = call_ctx.call.args[0].value
            # Parse URL parameters from query string
            if '?' in url:
                query_part = url.split('?', 1)[1]
                params = {}
                for param in query_part.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        # Try to convert to appropriate type
                        try:
                            if key in ['a', 'b']:
                                params[key] = float(value) if value != '' else None
                            else:
                                params[key] = value
                        except ValueError:
                            params[key] = value
                
                # Generate comprehensive mock request setup for API testing
                if 'operation' in params:
                    setup.append("    # Mock Flask request for API testing")
                    setup.append("    from unittest.mock import patch, MagicMock")
                    setup.append("    mock_request = MagicMock()")
                    setup.append("    mock_args = MagicMock()")
                    
                    # Setup the args.get method to return specific values based on key
                    setup.append("    def mock_args_get(key, type=None):")
                    for key, value in params.items():
                        if isinstance(value, str):
                            setup.append(f"        if key == '{key}': return '{value}'")
                        else:
                            setup.append(f"        if key == '{key}': return {value}")
                    setup.append("        return None")
                    setup.append("    mock_args.get = mock_args_get")
                    setup.append("    mock_request.args = mock_args")
                    
                    arg_refs = [f"# Flask API mock for: {url}"]
                    return setup, arg_refs
            else:
                # Handle cases without query parameters (like missing parameters tests)
                setup.append("    # Mock Flask request for API testing (no parameters)")
                setup.append("    from unittest.mock import patch, MagicMock")
                setup.append("    mock_request = MagicMock()")
                setup.append("    mock_request.args.get.return_value = None")
                arg_refs = ["# Flask API test with empty request"]
                return setup, arg_refs
    
    # Handle regular function calls
    # Handle positional arguments
    for idx, arg in enumerate(call_ctx.call.args):
        var_name = f"arg_{idx}"
        value = _resolve_argument_value(arg, call_ctx.local_vars)
        
        if value is _UNRESOLVED:
            return None  # Cannot resolve argument
        
        if _is_valid_argument_type(value):
            setup.append(f"    {var_name} = {repr(value)}")
            arg_refs.append(var_name)
        else:
            return None  # Invalid argument type
    
    # Handle keyword arguments
    for kw in call_ctx.call.keywords:
        if kw.arg is None:
            return None  # **kwargs not supported
        
        var_name = f"kw_{kw.arg}"
        value = _resolve_argument_value(kw.value, call_ctx.local_vars)
        
        if value is _UNRESOLVED:
            return None  # Cannot resolve keyword argument
        
        if _is_valid_argument_type(value):
            setup.append(f"    {var_name} = {repr(value)}")
            arg_refs.append(f"{kw.arg}={var_name}")
        else:
            return None  # Invalid argument type
    
    return setup, arg_refs


def _should_update_file(file_path: Path, new_content: str) -> bool:
    """Check if a file should be updated based on content changes.
    
    Args:
        file_path: Path to the file
        new_content: New content to write
        
    Returns:
        True if file should be updated, False otherwise
    """
    if not file_path.exists():
        return True
    
    new_hash = hashlib.sha256(new_content.encode()).hexdigest()
    old_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
    return old_hash != new_hash


def _build_seed_content(module_name: str, func_name: str, call_contexts: List[CallContext]) -> str:
    """Build the content for a seed file from call contexts.
    
    Args:
        module_name: Name of the module under test
        func_name: Name of the function under test
        call_contexts: List of call contexts to process
        
    Returns:
        Generated seed file content as string
    """
    lines: List[str] = [
        "# Auto-generated seed tests (normalised) - DO NOT EDIT MANUALLY",
        "# Generated by evolutionary_algo_integration.normalizer",
        "import sys",
        "from pathlib import Path",
        "",
        "# Add source directory to Python path",
        "current_dir = Path(__file__).parent",
        "source_dir = current_dir.parent / \"source\"",
        "sys.path.insert(0, str(source_dir))",
        "",
        f"import {module_name} as _mod",
        "",
    ]
    
    count = 0
    skipped = 0
    function_counts = {}  # Track how many seeds per function
    
    for call_ctx in call_contexts:
        try:
            resolved = _resolve_call_arguments(call_ctx)
            if resolved is None:
                skipped += 1
                continue
            
            setup, refs = resolved
            
            # Track function counts
            func_name = call_ctx.function_name
            if func_name not in function_counts:
                function_counts[func_name] = 0
            function_counts[func_name] += 1
            
            # Add comment indicating source test and target function
            lines.append(f"# From: {call_ctx.test_name} -> {call_ctx.function_name}")
            lines.append(f"def test_seed_{count}():")
            lines.extend(setup)
            
            # Special handling for API endpoint calls
            if (call_ctx.function_name == "calculate_api" and 
                isinstance(call_ctx.call.func, ast.Attribute) and 
                call_ctx.call.func.attr == "get"):
                lines.append(f"    with patch('{module_name}.request', mock_request):")
                lines.append(f"        _mod.{call_ctx.function_name}()")
            else:
                lines.append(f"    _mod.{call_ctx.function_name}({', '.join(refs)})")
            
            lines.append("")
            count += 1
            
        except Exception:
            # Skip problematic cases gracefully
            skipped += 1
            continue
    
    # Add summary with function breakdown
    if count == 0:
        lines.append("# No simplifiable calls found. Seeding will have no effect.")
    else:
        lines.append(f"# Generated {count} seed test cases from source tests")
        for func, func_count in function_counts.items():
            lines.append(f"# - {func}: {func_count} test cases")
        if skipped > 0:
            lines.append(f"# Skipped {skipped} cases due to complex expressions or unsupported types")
    
    return "\n".join(lines) + "\n"


def generate_seed_file(cfg: ExtractionConfig) -> Path:
    """Generate a Pynguin-compatible seed file from LLM-generated test files.
    
    This is the main entry point for seed file generation. It processes all
    raw test files in the specified directory and generates a consolidated
    seed file with normalized test cases.
    
    Args:
        cfg: Configuration object containing module name, function name, and tests directory
        
    Returns:
        Path to the generated seed file
        
    Raises:
        IOError: If there are issues reading test files or writing the seed file
    """
    all_calls: List[CallContext] = []
    
    # Auto-discover functions if enabled and no specific functions provided
    if cfg.auto_discover and not cfg.function_names:
        # Try to discover from source file
        source_path = cfg.tests_dir.parent / "source" / f"{cfg.module_name}.py"
        discovered_functions = _discover_functions_from_source(source_path)
        
        # Also discover from test files
        for test_file in _iter_raw_test_files(cfg.tests_dir):
            # Only process test files that match the module name
            if f"test_{cfg.module_name}" in test_file.name or f"{cfg.module_name}" in test_file.name:
                test_discovered = _discover_test_function_targets(test_file)
                discovered_functions.extend(test_discovered)
        
        # Remove duplicates and filter common test utilities
        discovered_functions = list(set(discovered_functions))
        cfg.function_names = discovered_functions
        print(f"Auto-discovered functions: {discovered_functions}")
    
    # Process all raw test files for all functions
    for file in _iter_raw_test_files(cfg.tests_dir):
        try:
            # Only process test files that match the module name
            if f"test_{cfg.module_name}" in file.name or f"{cfg.module_name}" in file.name:
                tree = ast.parse(file.read_text(encoding="utf-8"))
                # Extract calls for all specified functions
                for function_name in cfg.function_names:
                    calls = _extract_calls(tree, function_name)
                    all_calls.extend(calls)
        except SyntaxError:
            # Skip files with syntax errors
            continue
        except Exception:
            # Skip other problematic files gracefully
            continue

    # Generate seed file with Pynguin-compatible naming
    seed_name = f"test_{cfg.module_name}_seed.py"
    seed_path = cfg.tests_dir / seed_name
    # Use first function name for compatibility or "multiple" if more than one
    func_name_for_content = cfg.function_names[0] if len(cfg.function_names) == 1 else "multiple"
    content = _build_seed_content(cfg.module_name, func_name_for_content, all_calls)
    
    # Only update if content has changed (idempotent)
    if _should_update_file(seed_path, content):
        seed_path.write_text(content, encoding="utf-8")
    
    return seed_path


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(description="Normalize tests for Pynguin seeding")
    parser.add_argument("--tests-dir", required=True)
    parser.add_argument("--module-name", required=True)
    parser.add_argument("--function-name", help="Single function name (deprecated, use --function-names)")
    parser.add_argument("--function-names", nargs='+', 
                       help="One or more function names to extract tests for")
    parser.add_argument("--no-auto-discover", action="store_true",
                       help="Disable automatic function discovery")
    args = parser.parse_args()
    
    # Clean module name to remove .py extension if present
    module_name = args.module_name
    if module_name.endswith('.py'):
        module_name = module_name[:-3]
    
    # Handle backward compatibility and auto-discovery
    function_names = []
    auto_discover = not args.no_auto_discover
    
    if args.function_names:
        function_names = args.function_names
        auto_discover = False  # Explicit function names provided
    elif args.function_name:
        function_names = [args.function_name]
        auto_discover = False  # Explicit function name provided
    # If no functions specified and auto_discover is True, it will be handled in generate_seed_file
    
    cfg = ExtractionConfig(
        module_name=module_name,
        function_names=function_names,
        tests_dir=Path(args.tests_dir),
        auto_discover=auto_discover
    )
    out = generate_seed_file(cfg)
    print(f"Generated seed file: {out}")

if __name__ == "__main__":  # pragma: no cover
    main()
