"""
Module Parsing for ASTER-style static analysis.
Reads a Python file and parses it into an AST.
"""

import ast
from typing import Any

def parse_python_module(file_path: str) -> Any:
    # Reads the contents of a Python file and parses it into an AST.
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()
    tree = ast.parse(source, filename=file_path)
    return tree
