#!/usr/bin/env python3
#Source file analyzer for extracting function and class information.

import ast
from pathlib import Path
from typing import List, Dict, Set, Optional
import logging


class SourceAnalyzer:
    """Analyzer for extracting callable elements from Python source files."""
    
    def __init__(self, source_file: Path):
        self.source_file = source_file
        self.module_name = source_file.stem
        self._ast_tree = None
        self._functions = []
        self._classes = []
        self._methods = {}
        
    def _parse_ast(self) -> ast.AST:
        """Parse the source file into an AST tree."""
        if self._ast_tree is None:
            try:
                with open(self.source_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                self._ast_tree = ast.parse(content)
            except Exception as e:
                raise ValueError(f"Failed to parse {self.source_file}: {e}")
        return self._ast_tree
    
    def extract_functions(self) -> List[str]:
        #Extract all top-level function names from the source file.
        if self._functions:
            return self._functions
            
        tree = self._parse_ast()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Only include top-level functions (not nested or methods)
                for parent in ast.walk(tree):
                    if isinstance(parent, (ast.ClassDef, ast.FunctionDef)) and parent != node:
                        if node in ast.walk(parent):
                            break
                else:
                    # This is a top-level function
                    if not node.name.startswith('_'):  # Skip private functions
                        self._functions.append(node.name)
        
        return self._functions
    
    def extract_classes(self) -> List[str]:
        # Extract all class names from the source file.
        if self._classes:
            return self._classes
            
        tree = self._parse_ast()
        
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                if not node.name.startswith('_'):  # Skip private classes
                    self._classes.append(node.name)
        
        return self._classes
    
    def extract_methods(self, class_name: str) -> List[str]:
        # Extract method names from a specific class.
        if class_name in self._methods:
            return self._methods[class_name]
            
        tree = self._parse_ast()
        methods = []
        
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        if not item.name.startswith('_') or item.name in ['__init__', '__str__', '__repr__']:
                            methods.append(item.name)
        
        self._methods[class_name] = methods
        return methods
    
    def extract_all_callables(self) -> Dict[str, List[str]]:
        # Extract all callable elements (functions and methods) from the source file.
        result = {
            'functions': self.extract_functions(),
            'classes': {},
            'all_callables': []
        }
        
        # Add top-level functions
        result['all_callables'].extend(result['functions'])
        
        # Add methods from classes
        classes = self.extract_classes()
        for class_name in classes:
            methods = self.extract_methods(class_name)
            result['classes'][class_name] = methods
            # For simplicity, we'll focus on top-level functions for seed generation
            # Methods can be added later if needed
        
        return result
    
    def get_target_functions_for_testing(self) -> List[str]:
        # Get the list of functions that should be targeted for test generation.
        functions = self.extract_functions()
        
        # Filter out functions that shouldn't be tested directly
        excluded_patterns = [
            'main',  # Usually a script entry point
            'test_',  # Test functions
            'setup',  # Setup functions
            'teardown',  # Teardown functions
        ]
        
        filtered_functions = []
        for func in functions:
            if not any(func.startswith(pattern) for pattern in excluded_patterns):
                filtered_functions.append(func)
        
        return filtered_functions
    
    def analyze_complexity(self) -> Dict[str, int]:
        #Analyze the complexity of the source file.
        tree = self._parse_ast()
        
        # Count various AST nodes as complexity indicators
        complexity_metrics = {
            'total_nodes': 0,
            'functions': 0,
            'classes': 0,
            'conditional_statements': 0,
            'loops': 0,
            'lines_of_code': 0
        }
        
        for node in ast.walk(tree):
            complexity_metrics['total_nodes'] += 1
            
            if isinstance(node, ast.FunctionDef):
                complexity_metrics['functions'] += 1
            elif isinstance(node, ast.ClassDef):
                complexity_metrics['classes'] += 1
            elif isinstance(node, (ast.If, ast.IfExp)):
                complexity_metrics['conditional_statements'] += 1
            elif isinstance(node, (ast.For, ast.While)):
                complexity_metrics['loops'] += 1
        
        # Count lines of code
        try:
            with open(self.source_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                complexity_metrics['lines_of_code'] = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
        except Exception:
            complexity_metrics['lines_of_code'] = 0
        
        return complexity_metrics
    
    def __str__(self) -> str:
        """String representation of the analyzer."""
        functions = self.extract_functions()
        classes = self.extract_classes()
        return (f"SourceAnalyzer({self.module_name}): "
                f"{len(functions)} functions, {len(classes)} classes")


def analyze_source_file(source_file: Path) -> SourceAnalyzer:
    # Convenience function to create and return a SourceAnalyzer instance.
    return SourceAnalyzer(source_file)


def extract_functions_from_source(source_file: Path) -> List[str]:
    # Extract function names from a source file.
    analyzer = SourceAnalyzer(source_file)
    return analyzer.get_target_functions_for_testing()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python source_analyzer.py <source_file>")
        sys.exit(1)
    
    source_file = Path(sys.argv[1])
    if not source_file.exists():
        print(f"Error: Source file {source_file} does not exist")
        sys.exit(1)
    
    analyzer = SourceAnalyzer(source_file)
    
    print(f"Analysis of {source_file}:")
    print(f"Module: {analyzer.module_name}")
    print(f"Functions: {analyzer.extract_functions()}")
    print(f"Classes: {analyzer.extract_classes()}")
    print(f"Target functions for testing: {analyzer.get_target_functions_for_testing()}")
    
    complexity = analyzer.analyze_complexity()
    print(f"Complexity metrics: {complexity}")
