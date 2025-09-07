#!/usr/bin/env python3
"""
Cache Cleanup Script
This script removes all Python bytecode cache files and pytest cache directories from the entire project to prevent cache-related issues during testing.
"""

import os
import shutil
import subprocess
from pathlib import Path

def cleanup_caches_comprehensive():
    # Remove all cache files and directories from the project.
    workspace_root = Path(__file__).parent
    
    print("Starting comprehensive cache cleanup...")
    
    # Patterns to clean up
    cache_patterns = [
        "**/__pycache__",
        "**/.pytest_cache",
        "**/*.pyc",
        "**/*.pyo",
        "**/temp_test_dir/__pycache__",
        "**/tests/**/__pycache__",
        "**/mutants_validation/__pycache__",
        "**/initial_test_suite_generation/**/__pycache__",
        "**/evolutionary_algo_integration/**/__pycache__"
    ]
    
    removed_dirs = 0
    removed_files = 0
    
    # Remove __pycache__ directories
    for pattern in ["**/__pycache__", "**/.pytest_cache"]:
        for cache_dir in workspace_root.glob(pattern):
            if cache_dir.is_dir():
                try:
                    # Skip virtual environment directories
                    if any(venv in str(cache_dir) for venv in ['myvenv', 'mutpy_env', 'my_pynguin_venv']):
                        continue
                        
                    shutil.rmtree(cache_dir)
                    removed_dirs += 1
                    print(f"Removed directory: {cache_dir}")
                except Exception as e:
                    print(f"Could not remove {cache_dir}: {e}")
    
    # Remove .pyc and .pyo files
    for pattern in ["**/*.pyc", "**/*.pyo"]:
        for cache_file in workspace_root.glob(pattern):
            try:
                # Skip virtual environment directories
                if any(venv in str(cache_file) for venv in ['myvenv', 'mutpy_env', 'my_pynguin_venv']):
                    continue
                    
                cache_file.unlink()
                removed_files += 1
                print(f"Removed file: {cache_file}")
            except Exception as e:
                print(f"Could not remove {cache_file}: {e}")
    
    # Clear pytest cache using command
    try:
        result = subprocess.run(
            ['python', '-m', 'pytest', '--cache-clear'],
            capture_output=True,
            text=True,
            cwd=str(workspace_root)
        )
        if result.returncode == 0:
            print("Cleared pytest cache via command")
        else:
            print("Could not clear pytest cache via command")
    except Exception as e:
        print(f"Could not run pytest cache clear: {e}")
    
    # Set environment variable to prevent future cache creation
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    
    print(f"Cleanup complete!")
    print(f"Removed {removed_dirs} directories and {removed_files} files")
    print(f"PYTHONDONTWRITEBYTECODE=1 set to prevent future cache creation")
    
    return removed_dirs, removed_files

if __name__ == "__main__":
    cleanup_caches_comprehensive()
