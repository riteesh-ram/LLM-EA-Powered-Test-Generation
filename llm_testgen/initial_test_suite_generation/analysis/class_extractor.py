"""
Extract Class and Method Signatures and Details for static analysis.
Extracts comprehensive information about classes and their methods from an AST.
"""

import ast
from typing import List, Dict, Any, Optional


def extract_classes(tree: ast.AST) -> List[Dict[str, Any]]:
    # Extract all class signatures and details from an AST.
    classes = []
    
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            class_info = _extract_class_details(node)
            classes.append(class_info)
    
    return classes


def _extract_class_details(class_node: ast.ClassDef) -> Dict[str, Any]:

    # Extract detailed information from a class AST node.

    # Extract class name
    name = class_node.name
    
    # Extract docstring
    docstring = _extract_class_docstring(class_node)
    
    # Extract base classes
    base_classes = _extract_base_classes(class_node)
    
    # Extract decorators
    decorators = _extract_class_decorators(class_node)
    
    # Extract class variables
    class_variables = _extract_class_variables(class_node)
    
    # Extract methods
    init_method = None
    methods = []
    
    for node in class_node.body:
        if isinstance(node, ast.FunctionDef):
            method_info = _extract_method_details(node)
            if node.name == "__init__":
                init_method = method_info
            elif _is_public_method(node.name):
                methods.append(method_info)
    
    # Generate formatted signature
    signature = _format_class_signature(name, base_classes)
    
    return {
        'name': name,
        'docstring': docstring,
        'base_classes': base_classes,
        'decorators': decorators,
        'init_method': init_method,
        'methods': methods,
        'class_variables': class_variables,
        'signature': signature
    }


def _extract_method_details(method_node: ast.FunctionDef) -> Dict[str, Any]:
    # Extract detailed information from a method AST node.

    # Extract method name
    name = method_node.name
    
    # Extract parameters (excluding 'self' for instance methods)
    parameters = _extract_method_parameters(method_node.args)
    
    # Extract return type annotation
    return_type = _extract_type_annotation(method_node.returns) if method_node.returns else None
    
    # Extract docstring
    docstring = _extract_method_docstring(method_node)
    
    # Extract decorators
    decorators = _extract_method_decorators(method_node)
    
    # Determine method type
    method_type = _determine_method_type(method_node, decorators)
    
    # Generate formatted signature
    signature = _format_method_signature(name, parameters, return_type, method_type)
    
    return {
        'name': name,
        'parameters': parameters,
        'return_type': return_type,
        'docstring': docstring,
        'decorators': decorators,
        'method_type': method_type,
        'signature': signature
    }


def _extract_method_parameters(args: ast.arguments) -> List[Dict[str, Any]]:
    # Extract parameter information from method arguments (excluding self).
    parameters = []
    
    # Regular arguments (skip 'self' if present)
    method_args = args.args
    if method_args and method_args[0].arg in ('self', 'cls'):
        method_args = method_args[1:]  # Skip self/cls
    
    num_defaults = len(args.defaults)
    num_args = len(method_args)
    
    for i, arg in enumerate(method_args):
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


def _extract_base_classes(class_node: ast.ClassDef) -> List[str]:
    # Extract base class names from a class node.
    base_classes = []
    for base in class_node.bases:
        try:
            base_name = ast.unparse(base)
            base_classes.append(base_name)
        except Exception:
            if isinstance(base, ast.Name):
                base_classes.append(base.id)
            else:
                base_classes.append(str(base.__class__.__name__))
    return base_classes


def _extract_class_variables(class_node: ast.ClassDef) -> List[Dict[str, Any]]:
    # Extract class-level variables from a class node.
    class_vars = []
    
    for node in class_node.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    var_info = {
                        'name': target.id,
                        'type_annotation': None,
                        'value': _extract_default_value(node.value) if node.value else None
                    }
                    class_vars.append(var_info)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            var_info = {
                'name': node.target.id,
                'type_annotation': _extract_type_annotation(node.annotation) if node.annotation else None,
                'value': _extract_default_value(node.value) if node.value else None
            }
            class_vars.append(var_info)
    
    return class_vars


def _extract_class_docstring(class_node: ast.ClassDef) -> Optional[str]:
    # Extract docstring from a class node.
    if (class_node.body and 
        isinstance(class_node.body[0], ast.Expr) and 
        isinstance(class_node.body[0].value, ast.Constant) and 
        isinstance(class_node.body[0].value.value, str)):
        return class_node.body[0].value.value
    return None


def _extract_method_docstring(method_node: ast.FunctionDef) -> Optional[str]:
    # Extract docstring from a method node.
    if (method_node.body and 
        isinstance(method_node.body[0], ast.Expr) and 
        isinstance(method_node.body[0].value, ast.Constant) and 
        isinstance(method_node.body[0].value.value, str)):
        return method_node.body[0].value.value
    return None


def _extract_class_decorators(class_node: ast.ClassDef) -> List[str]:
    # Extract decorator names from a class node.
    decorators = []
    for decorator in class_node.decorator_list:
        try:
            decorator_name = ast.unparse(decorator)
            decorators.append(decorator_name)
        except Exception:
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
            else:
                decorators.append(str(decorator.__class__.__name__))
    return decorators


def _extract_method_decorators(method_node: ast.FunctionDef) -> List[str]:
    # Extract decorator names from a method node.
    decorators = []
    for decorator in method_node.decorator_list:
        try:
            decorator_name = ast.unparse(decorator)
            decorators.append(decorator_name)
        except Exception:
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
            else:
                decorators.append(str(decorator.__class__.__name__))
    return decorators


def _determine_method_type(method_node: ast.FunctionDef, decorators: List[str]) -> str:
    # Determine the type of method (instance, class, static).
    if 'staticmethod' in decorators:
        return 'static'
    elif 'classmethod' in decorators:
        return 'class'
    else:
        return 'instance'


def _is_public_method(method_name: str) -> bool:
    # Determine if a method is public (not starting with underscore).
    return not method_name.startswith('_')


def _extract_type_annotation(annotation: ast.expr) -> Optional[str]:
    # Extract type annotation as a string.
    try:
        return ast.unparse(annotation)
    except Exception:
        return str(annotation.__class__.__name__)


def _extract_default_value(default: ast.expr) -> Optional[str]:
    # Extract default value as a string.
    try:
        return ast.unparse(default)
    except Exception:
        if isinstance(default, ast.Constant):
            return repr(default.value)
        elif isinstance(default, ast.Name):
            return default.id
        else:
            return str(default.__class__.__name__)


def _format_class_signature(name: str, base_classes: List[str]) -> str:
    # Format a class signature string.
    if base_classes:
        bases_str = ", ".join(base_classes)
        return f"class {name}({bases_str})"
    else:
        return f"class {name}"


def _format_method_signature(name: str, parameters: List[Dict[str, Any]], 
                           return_type: Optional[str], method_type: str) -> str:
    # Format a method signature string.
    param_strings = []
    
    # Add self/cls parameter based on method type
    if method_type == 'instance':
        param_strings.append('self')
    elif method_type == 'class':
        param_strings.append('cls')
    # static methods don't have self/cls
    
    # Add other parameters
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