"""
Extract Imported Symbols (Constructors & Helpers) for ASTER-style static analysis.
Extracts comprehensive information about imported symbols from an AST.
"""

import ast
import importlib
import inspect
from typing import List, Dict, Any, Optional, Set


def extract_imports(tree: ast.AST) -> Dict[str, Any]:
    # Extract all imported symbols and their details from an AST.
    imports_data = {
        'standard_imports': [],
        'third_party_imports': [],
        'local_imports': [],
        'import_statements': [],
        'symbol_map': {},
        'available_symbols': []
    }
    
    available_symbols = set()
    
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            import_details = _extract_import_details(node)
            imports_data['import_statements'].append(import_details['statement'])
            
            for item in import_details['items']:
                available_symbols.add(item['local_name'])
                imports_data['symbol_map'][item['local_name']] = item['module_path']
                _categorize_import(item, imports_data)
                
        elif isinstance(node, ast.ImportFrom):
            import_details = _extract_import_from_details(node)
            imports_data['import_statements'].append(import_details['statement'])
            
            for item in import_details['items']:
                available_symbols.add(item['local_name'])
                imports_data['symbol_map'][item['local_name']] = item['module_path']
                _categorize_import(item, imports_data)
    
    imports_data['available_symbols'] = sorted(list(available_symbols))
    
    # Try to resolve signatures for imported symbols
    _resolve_import_signatures(imports_data)
    
    return imports_data


def _extract_import_details(import_node: ast.Import) -> Dict[str, Any]:
    # Extract details from an ast.Import node.
    items = []
    statement_parts = []
    
    for alias in import_node.names:
        module_name = alias.name
        local_name = alias.asname if alias.asname else alias.name
        
        items.append({
            'original_name': module_name,
            'local_name': local_name,
            'module_path': module_name,
            'import_type': 'module'
        })
        
        if alias.asname:
            statement_parts.append(f"{module_name} as {alias.asname}")
        else:
            statement_parts.append(module_name)
    
    statement = f"import {', '.join(statement_parts)}"
    
    return {
        'statement': statement,
        'items': items
    }


def _extract_import_from_details(import_from_node: ast.ImportFrom) -> Dict[str, Any]:
    # Extract details from an ast.ImportFrom node.
    module = import_from_node.module or ""
    level = import_from_node.level
    
    # Handle relative imports
    if level > 0:
        module = "." * level + (module if module else "")
    
    items = []
    statement_parts = []
    
    for alias in import_from_node.names:
        original_name = alias.name
        local_name = alias.asname if alias.asname else alias.name
        
        items.append({
            'original_name': original_name,
            'local_name': local_name,
            'module_path': module,
            'import_type': 'symbol',
            'is_relative': level > 0
        })
        
        if alias.asname:
            statement_parts.append(f"{original_name} as {alias.asname}")
        else:
            statement_parts.append(original_name)
    
    statement = f"from {module} import {', '.join(statement_parts)}"
    
    return {
        'module': module,
        'statement': statement,
        'items': items,
        'level': level
    }


def _categorize_import(import_item: Dict[str, Any], imports_data: Dict[str, Any]) -> None:
    # Categorize an import item as standard library, third-party, or local.
    module_path = import_item['module_path']
    
    # Check if it's a relative import
    if import_item.get('is_relative', False):
        imports_data['local_imports'].append(import_item)
        return
    
    # Extract top-level module name
    top_level_module = module_path.split('.')[0]
    
    # Check if it's a standard library module
    if _is_standard_library(top_level_module):
        imports_data['standard_imports'].append(import_item)
    elif _is_local_module(module_path):
        imports_data['local_imports'].append(import_item)
    else:
        imports_data['third_party_imports'].append(import_item)


def _is_standard_library(module_name: str) -> bool:
    # Check if a module is part of the Python standard library.
    # Common standard library modules
    stdlib_modules = {
        'os', 'sys', 'json', 'csv', 'math', 'random', 'datetime', 'time',
        'collections', 'itertools', 'functools', 'operator', 'pathlib',
        'typing', 'abc', 're', 'urllib', 'http', 'email', 'html', 'xml',
        'sqlite3', 'pickle', 'copy', 'deepcopy', 'io', 'tempfile',
        'unittest', 'logging', 'argparse', 'configparser', 'hashlib',
        'base64', 'binascii', 'struct', 'array', 'weakref', 'gc',
        'threading', 'multiprocessing', 'asyncio', 'concurrent',
        'subprocess', 'shutil', 'glob', 'fnmatch', 'stat', 'platform'
    }
    
    if module_name in stdlib_modules:
        return True
    
    # Try to check if it's importable from standard library
    try:
        module = importlib.import_module(module_name)
        if hasattr(module, '__file__') and module.__file__:
            # Check if it's in stdlib path
            import sys
            stdlib_paths = [p for p in sys.path if 'site-packages' not in p and 'dist-packages' not in p]
            return any(module.__file__.startswith(p) for p in stdlib_paths)
        return True  # Built-in modules don't have __file__
    except ImportError:
        return False


def _is_local_module(module_path: str) -> bool:
    # Check if a module is likely a local module.
    # Simple heuristic: if it starts with a dot or contains common local patterns
    return (module_path.startswith('.') or 
            any(part in module_path.lower() for part in ['local', 'src', 'lib', 'utils']))


def _resolve_import_signatures(imports_data: Dict[str, Any]) -> None:
    # Try to resolve signatures for imported symbols (advanced feature).
    for category in ['standard_imports', 'third_party_imports']:
        for import_item in imports_data[category]:
            signature_info = _get_symbol_signature(import_item)
            if signature_info:
                import_item['signature_info'] = signature_info


def _get_symbol_signature(import_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    # Try to get the signature of an imported symbol.
    try:
        module_path = import_item['module_path']
        local_name = import_item['local_name']
        
        if import_item['import_type'] == 'module':
            # For module imports, get public attributes
            module = importlib.import_module(module_path)
            public_attrs = _get_module_public_attributes(module)
            return {
                'type': 'module',
                'name': local_name,
                'public_attributes': public_attrs[:10]  # Limit to first 10
            }
        else:
            # For symbol imports, try to get the actual symbol
            module = importlib.import_module(module_path)
            symbol = getattr(module, import_item['original_name'], None)
            if symbol is None:
                return None
                
            if inspect.isclass(symbol):
                return _get_class_signature(symbol, local_name)
            elif inspect.isfunction(symbol):
                return _get_function_signature(symbol, local_name)
            else:
                return {
                    'type': 'other',
                    'name': local_name,
                    'python_type': type(symbol).__name__
                }
                
    except Exception:
        # If we can't resolve the signature, it's not critical
        return None


def _get_module_public_attributes(module) -> List[str]:
    # Get public attributes of a module.
    try:
        if hasattr(module, '__all__'):
            return list(module.__all__)
        else:
            return [attr for attr in dir(module) if not attr.startswith('_')]
    except Exception:
        return []


def _get_class_signature(cls, local_name: str) -> Dict[str, Any]:
    # Get signature information for a class.
    try:
        init_signature = None
        if hasattr(cls, '__init__'):
            try:
                init_signature = str(inspect.signature(cls.__init__))
            except Exception:
                init_signature = None
        
        return {
            'type': 'class',
            'name': local_name,
            'init_signature': init_signature,
            'doc': getattr(cls, '__doc__', None)
        }
    except Exception:
        return {
            'type': 'class',
            'name': local_name,
            'init_signature': None,
            'doc': None
        }


def _get_function_signature(func, local_name: str) -> Dict[str, Any]:
    # Get signature information for a function.
    try:
        signature = str(inspect.signature(func))
        return {
            'type': 'function',
            'name': local_name,
            'signature': signature,
            'doc': getattr(func, '__doc__', None)
        }
    except Exception:
        return {
            'type': 'function',
            'name': local_name,
            'signature': None,
            'doc': None
        }