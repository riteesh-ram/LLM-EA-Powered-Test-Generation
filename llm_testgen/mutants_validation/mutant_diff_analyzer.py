#!/usr/bin/env python3
"""
Mutant Diff Analyzer

Analyzes differences between original source code and mutants,
showing exactly which lines changed and what the changes are.
"""

import difflib
import os
from pathlib import Path
from typing import List, Dict, Tuple


class MutantDiffAnalyzer:
    """Analyzes and reports differences between original and mutant files."""
    
    def __init__(self):
        """Initialize the analyzer."""
        pass
    
    def analyze_mutant_diff(self, original_file: Path, mutant_file: Path) -> Dict:
        #Analyze differences between original and mutant files.

        try:
            # Read file contents
            with open(original_file, 'r') as f:
                original_lines = f.readlines()
            
            with open(mutant_file, 'r') as f:
                mutant_lines = f.readlines()
            
            # Get unified diff
            diff_lines = list(difflib.unified_diff(
                original_lines,
                mutant_lines,
                fromfile=f"original/{original_file.name}",
                tofile=f"mutant/{mutant_file.name}",
                lineterm=''
            ))
            
            # Extract changed lines
            changes = self._extract_changes(original_lines, mutant_lines)
            
            # Generate summary
            summary = self._generate_change_summary(changes, mutant_file.name)
            
            return {
                'mutant_file': mutant_file.name,
                'diff_lines': diff_lines,
                'changes': changes,
                'summary': summary,
                'num_changes': len(changes)
            }
            
        except Exception as e:
            return {
                'mutant_file': mutant_file.name,
                'error': str(e),
                'summary': f"Error analyzing {mutant_file.name}: {str(e)}"
            }
    
    def _extract_changes(self, original_lines: List[str], mutant_lines: List[str]) -> List[Dict]:
        """Extract specific line changes between original and mutant."""
        changes = []
        
        # Use difflib to find differences
        matcher = difflib.SequenceMatcher(None, original_lines, mutant_lines)
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace':
                # Lines were modified
                for k in range(max(i2-i1, j2-j1)):
                    orig_idx = i1 + k
                    mut_idx = j1 + k
                    
                    orig_line = original_lines[orig_idx].rstrip() if orig_idx < len(original_lines) else ""
                    mut_line = mutant_lines[mut_idx].rstrip() if mut_idx < len(mutant_lines) else ""
                    
                    if orig_line != mut_line:
                        changes.append({
                            'line_number': orig_idx + 1,
                            'change_type': 'modified',
                            'original': orig_line,
                            'mutated': mut_line
                        })
            
            elif tag == 'delete':
                # Lines were deleted
                for k in range(i2 - i1):
                    orig_idx = i1 + k
                    changes.append({
                        'line_number': orig_idx + 1,
                        'change_type': 'deleted',
                        'original': original_lines[orig_idx].rstrip(),
                        'mutated': ""
                    })
            
            elif tag == 'insert':
                # Lines were inserted
                for k in range(j2 - j1):
                    mut_idx = j1 + k
                    changes.append({
                        'line_number': i1 + 1,  # Insert position in original
                        'change_type': 'inserted',
                        'original': "",
                        'mutated': mutant_lines[mut_idx].rstrip()
                    })
        
        return changes
    
    def _generate_change_summary(self, changes: List[Dict], mutant_name: str) -> str:
        """Generate a human-readable summary of changes."""
        if not changes:
            return f"No changes detected in {mutant_name}"
        
        summary_lines = [f"\n=== MUTANT: {mutant_name} ==="]
        summary_lines.append(f"Total changes: {len(changes)}")
        summary_lines.append("")
        
        for change in changes:
            line_num = change['line_number']
            change_type = change['change_type']
            original = change['original']
            mutated = change['mutated']
            
            summary_lines.append(f"Line {line_num} ({change_type}):")
            
            if change_type == 'modified':
                summary_lines.append(f"  - Original: {original}")
                summary_lines.append(f"  + Mutated:  {mutated}")
            elif change_type == 'deleted':
                summary_lines.append(f"  - Deleted:  {original}")
            elif change_type == 'inserted':
                summary_lines.append(f"  + Inserted: {mutated}")
            
            summary_lines.append("")
        
        return "\n".join(summary_lines)
    
    def analyze_all_mutants(self, original_file: Path, mutants_dir: Path) -> List[Dict]:
        #Analyze all mutants in the given directory.

        results = []
        
        # Find all mutant files
        mutant_files = []
        for file in mutants_dir.iterdir():
            if file.is_file() and file.suffix == '.py' and file.name != original_file.name:
                mutant_files.append(file)
        
        print(f"Found {len(mutant_files)} mutant files to analyze")
        
        for mutant_file in sorted(mutant_files):
            print(f"Analyzing: {mutant_file.name}")
            result = self.analyze_mutant_diff(original_file, mutant_file)
            results.append(result)
            
            # Print summary for each mutant
            if 'summary' in result:
                print(result['summary'])
            
        return results


def main():
    """Example usage of the mutant diff analyzer."""
    analyzer = MutantDiffAnalyzer()
    
    # Example paths - adjust these for your setup
    original_file = Path("../tests/sample_calculator.py")  # Adjust path
    mutants_dir = Path("generated_mutants")
    
    if original_file.exists() and mutants_dir.exists():
        print(f"Analyzing mutants for: {original_file}")
        print(f"Mutants directory: {mutants_dir}")
        
        results = analyzer.analyze_all_mutants(original_file, mutants_dir)
        
        print(f"\n=== ANALYSIS COMPLETE ===")
        print(f"Total mutants analyzed: {len(results)}")
        
        # Summary of all changes
        total_changes = sum(r.get('num_changes', 0) for r in results)
        print(f"Total changes detected: {total_changes}")
        
    else:
        print("Original file or mutants directory not found!")
        print(f"Original file: {original_file} (exists: {original_file.exists()})")
        print(f"Mutants dir: {mutants_dir} (exists: {mutants_dir.exists()})")


if __name__ == "__main__":
    main()
