"""
Extract Top-Level Function Signatures and Details for ASTER-style static analysis.
Extracts comprehensive information about top-level functions from an AST.
"""

import ast
from typing import List, Dict, Any, Optional


def extract_top_level_functions(tree: ast.AST) -> List[Dict[str, Any]]:
    # Extract all top-level function signatures and details from an AST.
    functions = []
    
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef):
            function_info = _extract_function_details(node)
            functions.append(function_info)
    
    return functions


def _extract_function_details(func_node: ast.FunctionDef) -> Dict[str, Any]:
    # Extract detailed information from a function AST node.
    # Extract function name
    name = func_node.name
    
    # Extract parameters
    parameters = _extract_parameters(func_node.args)
    
    # Extract return type annotation
    return_type = _extract_type_annotation(func_node.returns) if func_node.returns else None
    
    # Extract docstring
    docstring = _extract_docstring(func_node)
    
    # Extract decorators
    decorators = _extract_decorators(func_node)
    
    # Generate formatted signature
    signature = _format_function_signature(name, parameters, return_type)
    
    return {
        'name': name,
        'parameters': parameters,
        'return_type': return_type,
        'docstring': docstring,
        'decorators': decorators,
        'signature': signature
    }


def _extract_parameters(args: ast.arguments) -> List[Dict[str, Any]]:
    # Extract parameter information from function arguments.
    parameters = []
    
    # Regular arguments
    num_defaults = len(args.defaults)
    num_args = len(args.args)
    
    for i, arg in enumerate(args.args):
        # Calculate if this parameter has a default value
        default_index = i - (num_args - num_defaults)
        default_value = None
        
        if default_index >= 0:
            default_value = _extract_default_value(args.defaults[default_index])
        
        param_info = {
            'name': arg.arg,
            'type_annotation': _extract_type_annotation(arg.annotation) if arg.annotation else None,
            'default_value': default_value,
            'kind': 'regular'
        }
        parameters.append(param_info)
    
    # *args parameter
    if args.vararg:
        param_info = {
            'name': args.vararg.arg,
            'type_annotation': _extract_type_annotation(args.vararg.annotation) if args.vararg.annotation else None,
            'default_value': None,
            'kind': 'vararg'
        }
        parameters.append(param_info)
    
    # Keyword-only arguments
    for i, arg in enumerate(args.kwonlyargs):
        default_value = None
        if i < len(args.kw_defaults) and args.kw_defaults[i] is not None:
            default_value = _extract_default_value(args.kw_defaults[i])
        
        param_info = {
            'name': arg.arg,
            'type_annotation': _extract_type_annotation(arg.annotation) if arg.annotation else None,
            'default_value': default_value,
            'kind': 'keyword_only'
        }
        parameters.append(param_info)
    
    # **kwargs parameter
    if args.kwarg:
        param_info = {
            'name': args.kwarg.arg,
            'type_annotation': _extract_type_annotation(args.kwarg.annotation) if args.kwarg.annotation else None,
            'default_value': None,
            'kind': 'kwarg'
        }
        parameters.append(param_info)
    
    return parameters


def _extract_type_annotation(annotation: ast.expr) -> Optional[str]:
    # Extract type annotation as a string.
    try:
        return ast.unparse(annotation)
    except Exception:
        # Fallback for older Python versions or complex annotations
        return str(annotation.__class__.__name__)


def _extract_default_value(default: ast.expr) -> Optional[str]:
    # Extract default value as a string.
    try:
        return ast.unparse(default)
    except Exception:
        # Fallback for complex default values
        if isinstance(default, ast.Constant):
            return repr(default.value)
        elif isinstance(default, ast.Name):
            return default.id
        else:
            return str(default.__class__.__name__)


def _extract_docstring(func_node: ast.FunctionDef) -> Optional[str]:
    # Extract docstring from a function node.
    if (func_node.body and 
        isinstance(func_node.body[0], ast.Expr) and 
        isinstance(func_node.body[0].value, ast.Constant) and 
        isinstance(func_node.body[0].value.value, str)):
        return func_node.body[0].value.value
    return None


def _extract_decorators(func_node: ast.FunctionDef) -> List[str]:
    # Extract decorator names from a function node.
    decorators = []
    for decorator in func_node.decorator_list:
        try:
            decorator_name = ast.unparse(decorator)
            decorators.append(decorator_name)
        except Exception:
            # Fallback for complex decorators
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
            else:
                decorators.append(str(decorator.__class__.__name__))
    return decorators


def _format_function_signature(name: str, parameters: List[Dict[str, Any]], return_type: Optional[str]) -> str:
    # Format a complete function signature string.
    param_strings = []
    
    for param in parameters:
        param_str = param['name']
        
        # Add type annotation
        if param['type_annotation']:
            param_str += f": {param['type_annotation']}"
        
        # Add default value
        if param['default_value'] is not None:
            param_str += f" = {param['default_value']}"
        
        # Add special prefixes for *args and **kwargs
        if param['kind'] == 'vararg':
            param_str = f"*{param_str}"
        elif param['kind'] == 'kwarg':
            param_str = f"**{param_str}"
        
        param_strings.append(param_str)
    
    # Join parameters
    params_str = ", ".join(param_strings)
    
    # Add return type
    return_str = f" -> {return_type}" if return_type else ""
    
    return f"def {name}({params_str}){return_str}"