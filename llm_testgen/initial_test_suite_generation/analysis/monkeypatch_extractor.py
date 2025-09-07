"""
Identify Monkeypatch/Mock Points for ASTER-style static analysis.
Finds calls to external APIs, I/O, or library functions that should be monkeypatched in tests.
"""

import ast
import json
from typing import List, Dict, Any, Set, Optional


# Default external modules that commonly need monkeypatching
DEFAULT_EXTERNAL_MODULES = {
    # Network and HTTP
    'requests', 'urllib', 'http', 'httpx', 'aiohttp',
    # File system and I/O
    'os', 'shutil', 'pathlib', 'tempfile', 'glob',
    # System and environment
    'sys', 'platform', 'subprocess', 'signal',
    # Date and time
    'time', 'datetime', 'calendar',
    # Random and crypto
    'random', 'secrets', 'uuid', 'hashlib',
    # Database
    'sqlite3', 'pymongo', 'psycopg2', 'mysql',
    # External services
    'boto3', 'azure', 'google', 'stripe', 'twilio',
    # Email and messaging
    'smtplib', 'email', 'mailgun', 'sendgrid',
    # Configuration and environment
    'configparser', 'dotenv', 'environ',
    # Logging and monitoring
    'logging', 'sentry_sdk', 'datadog',
    # Third-party APIs
    'github', 'slack', 'discord', 'twitter'
}

# Built-in functions that commonly need monkeypatching
DEFAULT_BUILTIN_FUNCTIONS = {
    'open', 'input', 'print', 'exit', 'quit'
}

# Common I/O and external operation patterns
EXTERNAL_PATTERNS = {
    # File operations
    'file_operations': ['open', 'read', 'write', 'close', 'remove', 'mkdir', 'rmdir'],
    # Network operations
    'network_operations': ['get', 'post', 'put', 'delete', 'patch', 'request', 'urlopen'],
    # System operations
    'system_operations': ['system', 'popen', 'run', 'call', 'check_output'],
    # Database operations
    'database_operations': ['connect', 'execute', 'commit', 'rollback', 'close'],
    # Time operations
    'time_operations': ['sleep', 'time', 'now', 'today', 'strftime'],
    # Random operations
    'random_operations': ['random', 'randint', 'choice', 'shuffle', 'seed']
}


def identify_monkeypatch_points(tree: ast.AST, 
                              external_modules: Optional[Set[str]] = None,
                              builtin_functions: Optional[Set[str]] = None,
                              custom_patterns: Optional[Dict[str, List[str]]] = None) -> Dict[str, Any]:
    # Identify all calls that should be monkeypatched in tests.
    if external_modules is None:
        external_modules = DEFAULT_EXTERNAL_MODULES
    if builtin_functions is None:
        builtin_functions = DEFAULT_BUILTIN_FUNCTIONS
    if custom_patterns is None:
        custom_patterns = EXTERNAL_PATTERNS
    
    monkeypatch_data = {
        'external_calls': [],
        'builtin_calls': [],
        'file_operations': [],
        'network_operations': [],
        'system_operations': [],
        'database_operations': [],
        'time_operations': [],
        'random_operations': [],
        'all_monkeypatch_targets': [],
        'call_contexts': []
    }
    
    # Walk the AST to find all function calls
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            call_info = _analyze_call_node(node, external_modules, builtin_functions, custom_patterns)
            if call_info:
                _categorize_call(call_info, monkeypatch_data, custom_patterns)
    
    # Remove duplicates and sort
    _deduplicate_and_sort(monkeypatch_data)
    
    return monkeypatch_data


def _analyze_call_node(call_node: ast.Call, 
                      external_modules: Set[str],
                      builtin_functions: Set[str],
                      custom_patterns: Dict[str, List[str]]) -> Optional[Dict[str, Any]]:
    # Analyze a call node to determine if it should be monkeypatched.
    call_info = _extract_call_details(call_node)
    
    if not call_info:
        return None
    
    # Check if it's an external module call
    if call_info['module'] and call_info['module'] in external_modules:
        call_info['category'] = 'external'
        call_info['reason'] = f"External module: {call_info['module']}"
        return call_info
    
    # Check if it's a builtin function call
    if call_info['function'] in builtin_functions:
        call_info['category'] = 'builtin'
        call_info['reason'] = f"Builtin function: {call_info['function']}"
        return call_info
    
    # Check if it matches any custom patterns
    for pattern_category, pattern_functions in custom_patterns.items():
        if call_info['function'] in pattern_functions:
            call_info['category'] = pattern_category
            call_info['reason'] = f"Pattern match: {pattern_category}"
            return call_info
    
    # Check for common external operation patterns in method names
    if _is_likely_external_operation(call_info['full_call']):
        call_info['category'] = 'external'
        call_info['reason'] = "Likely external operation"
        return call_info
    
    return None


def _extract_call_details(call_node: ast.Call) -> Optional[Dict[str, Any]]:
    # Extract details from a call node.
    try:
        # Get the function being called
        func = call_node.func
        
        if isinstance(func, ast.Name):
            # Simple function call: func()
            return {
                'function': func.id,
                'module': None,
                'object': None,
                'full_call': func.id,
                'args_count': len(call_node.args),
                'kwargs_count': len(call_node.keywords),
                'line_number': getattr(call_node, 'lineno', None)
            }
        elif isinstance(func, ast.Attribute):
            # Method call: obj.method() or module.function()
            obj_name = _get_object_name(func.value)
            method_name = func.attr
            full_call = f"{obj_name}.{method_name}" if obj_name else method_name
            
            return {
                'function': method_name,
                'module': obj_name if obj_name and not obj_name.islower() else None,
                'object': obj_name,
                'full_call': full_call,
                'args_count': len(call_node.args),
                'kwargs_count': len(call_node.keywords),
                'line_number': getattr(call_node, 'lineno', None)
            }
        
        return None
        
    except Exception:
        return None


def _get_object_name(node: ast.expr) -> Optional[str]:
    # Get the name of an object from an AST node.
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        parent = _get_object_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    else:
        return None


def _is_likely_external_operation(call_name: str) -> bool:
    # Check if a call name suggests an external operation.
    if not call_name:
        return False
    
    # Common patterns that suggest external operations
    external_indicators = [
        'fetch', 'download', 'upload', 'send', 'receive',
        'connect', 'disconnect', 'login', 'logout', 'authenticate',
        'create_file', 'delete_file', 'read_file', 'write_file',
        'execute', 'run_command', 'shell', 'subprocess',
        'http_', 'api_', 'rest_', 'ws_', 'socket_',
        'db_', 'database_', 'sql_', 'query_',
        'cache_', 'redis_', 'memcache_',
        'email_', 'smtp_', 'mail_',
        'log_', 'logger_', 'audit_'
    ]
    
    call_lower = call_name.lower()
    return any(indicator in call_lower for indicator in external_indicators)


def _categorize_call(call_info: Dict[str, Any], 
                    monkeypatch_data: Dict[str, Any],
                    custom_patterns: Dict[str, List[str]]) -> None:
    # Categorize a call into the appropriate monkeypatch category.
    category = call_info.get('category', 'unknown')
    full_call = call_info['full_call']
    
    # Add to general lists
    if category == 'external':
        monkeypatch_data['external_calls'].append(call_info)
    elif category == 'builtin':
        monkeypatch_data['builtin_calls'].append(call_info)
    
    # Add to specific pattern categories
    if category in custom_patterns:
        if category not in monkeypatch_data:
            monkeypatch_data[category] = []
        monkeypatch_data[category].append(call_info)
    
    # Add to all targets list
    monkeypatch_data['all_monkeypatch_targets'].append(full_call)
    
    # Add context information
    context = {
        'target': full_call,
        'category': category,
        'reason': call_info.get('reason', ''),
        'location': f"line {call_info.get('line_number', '?')}",
        'args_count': call_info['args_count'],
        'kwargs_count': call_info['kwargs_count']
    }
    monkeypatch_data['call_contexts'].append(context)


def _deduplicate_and_sort(monkeypatch_data: Dict[str, Any]) -> None:
    # Remove duplicates and sort the monkeypatch data.
    # Deduplicate all_monkeypatch_targets
    monkeypatch_data['all_monkeypatch_targets'] = sorted(list(set(monkeypatch_data['all_monkeypatch_targets'])))
    
    # Sort call contexts by target
    monkeypatch_data['call_contexts'].sort(key=lambda x: x['target'])


def load_custom_config(config_path: str) -> Dict[str, Any]:
    # Load custom monkeypatch configuration from a file.
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        external_modules = set(config.get('external_modules', []))
        builtin_functions = set(config.get('builtin_functions', []))
        custom_patterns = config.get('custom_patterns', {})
        
        return {
            'external_modules': external_modules,
            'builtin_functions': builtin_functions,
            'custom_patterns': custom_patterns
        }
    except Exception:
        return {
            'external_modules': DEFAULT_EXTERNAL_MODULES,
            'builtin_functions': DEFAULT_BUILTIN_FUNCTIONS,
            'custom_patterns': EXTERNAL_PATTERNS
        }