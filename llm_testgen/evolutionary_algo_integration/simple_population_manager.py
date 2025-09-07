#!/usr/bin/env python3
"""
Simple Population Size Manager for Pynguin.

This module analyzes code complexity and updates Pynguin's population size automatically.
"""

import re
from pathlib import Path
from dataclasses import dataclass
from radon.raw import analyze
from radon.complexity import cc_visit
from radon.metrics import mi_parameters


@dataclass
class ComplexityMetrics:
    """Container for complexity metrics."""
    cyclomatic_complexity: int
    halstead_volume: float
    sloc: int  # Source Lines of Code


class SimpleComplexityAnalyzer:
    """Analyzes code complexity using radon library and computes population size."""
    
    def analyze_file(self, file_path: str) -> ComplexityMetrics:
        """Analyze a Python file and return complexity metrics."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            return self.analyze_code(code)
        except Exception:
            return ComplexityMetrics(1, 0.0, 1)  # Fallback
    
    def analyze_code(self, code: str) -> ComplexityMetrics:
        """Analyze Python code and return complexity metrics using radon."""
        try:
            # 1. Get SLOC (Source Lines of Code)
            raw_metrics = analyze(code)
            sloc = raw_metrics.sloc  # Source lines (excluding blanks and comments)
            
            # 2. Get Cyclomatic Complexity
            cc_results = cc_visit(code)
            cyclomatic_complexity = sum(item.complexity for item in cc_results) if cc_results else 1
            
            # 3. Get Halstead Volume
            try:
                halstead_volume, _, _, _ = mi_parameters(code)
            except:
                halstead_volume = 0.0
            
            return ComplexityMetrics(cyclomatic_complexity, halstead_volume, sloc)
        except:
            return ComplexityMetrics(1, 0.0, 1)
    
    def compute_population_size(self, metrics: ComplexityMetrics) -> int:
        """Compute population size based on complexity metrics."""
        # Adjust normalization factors to be more sensitive to moderate complexity
        cc_norm = min(1.0, metrics.cyclomatic_complexity / 35.0)
        hv_norm = min(1.0, metrics.halstead_volume / 700.0)
        sloc_norm = min(1.0, metrics.sloc / 350.0)
        
        # Adjusted weighted combination to emphasize cyclomatic complexity more
        complexity_score = 0.45 * cc_norm + 0.35 * hv_norm + 0.20 * sloc_norm
        
        # Scale from base size 50 to max 200
        population_size = int(50 * (1 + 3 * complexity_score))
        return max(50, min(population_size, 200))


def auto_adjust_population_for_module(module_name: str) -> int:
    """
    Analyze module and update Pynguin population size.
    """
    # Find source file in tests/source directory
    source_dir = Path(__file__).parent.parent / "tests" / "source"
    source_file = source_dir / f"{module_name}.py"
    
    if not source_file.exists():
        return 80  # Default fallback
    
    # Analyze complexity
    analyzer = SimpleComplexityAnalyzer()
    metrics = analyzer.analyze_file(str(source_file))
    population_size = analyzer.compute_population_size(metrics)
    
    # Display analysis
    print(f"\nComplexity Analysis for {module_name}.py:")
    print(f"   • Cyclomatic Complexity: {metrics.cyclomatic_complexity}")
    print(f"   • Halstead Volume: {metrics.halstead_volume:.1f}")
    print(f"   • Source Lines of Code: {metrics.sloc}")
    print(f"Computed Population Size: {population_size}")
    
    # Update Pynguin configuration
    config_path = Path(__file__).parent.parent / "pynguin-main" / "src" / "pynguin" / "configuration.py"
    
    try:
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Find and update population value
        pattern = r'(\s+population: int = )(\d+)'
        match = re.search(pattern, content)
        
        if match:
            current_value = int(match.group(2))
            if current_value != population_size:
                replacement = f'{match.group(1)}{population_size}'
                new_content = re.sub(pattern, replacement, content)
                with open(config_path, 'w') as f:
                    f.write(new_content)
                print(f"Updated population size: {current_value} → {population_size}")
            else:
                print(f"Population size already set to {population_size}")
        else:
            print(f"Could not find population setting to update")
    except Exception:
        print(f"Failed to update Pynguin configuration")
    
    return population_size
