import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, call
import runpy
import importlib
import io # Required to capture stdout

# Add the tests/source directory to Python path
current_dir = Path(__file__).parent
source_dir = current_dir.parent / "source"
sys.path.insert(0, str(source_dir))

# Corrected import: The mutants are for 'sample_utility', as indicated by the mutant names
# and the existing test suite's import structure.
import sample_utility
# Removed 'from sample_utility import classify_numbers' as it's not present in the provided
# source code's functionality and is likely a leftover from a template.

class TestKillerMutants:
    """Killer tests for surviving mutants."""

    def test_kill_mutant_main_block_execution_and_fibonacci_print_guard(self, monkeypatch):
        """
        Kills Mutant 1: `if __name__ == "__main__":` -> `if not (__name__ == '__main__'):`
        Kills Mutant 4: `if __name__ == "__main__":` -> `if __name__ != '__main__':`
        Kills Mutant 2: `if fib_sequence:` -> `if not fib_sequence:`

        This test runs the `sample_utility` module directly (simulating `python sample_utility.py`)
        and asserts that the expected Fibonacci example usage output is printed.
        It assumes `sample_utility.py` has an `if __name__ == "__main__":` block similar
        to the `math_utils.py` provided in the prompt.

        On original: The `if __name__ == "__main__":` block executes, `fib_sequence` is
                     a non-empty list, so the print statement for Fibonacci runs. Test passes.

        On Mutant 1 & 4: The `if __name__ == "__main__":` guard is inverted. When run directly,
                         `__name__` is `'__main__'`, making the inverted condition `False`.
                         The entire example usage block will not execute, so the expected
                         print statements will be missing. Test fails.

        On Mutant 2: The `if fib_sequence:` guard is inverted to `if not fib_sequence:`.
                     Since `fib_sequence` (e.g., `[0, 1, ..., 34]`) is truthy, `not fib_sequence`
                     evaluates to `False`. The print statement for the Fibonacci sequence
                     will be skipped. Test fails.
        """
        # Arrange
        # Use io.StringIO to capture anything printed to sys.stdout
        captured_output = io.StringIO()
        monkeypatch.setattr(sys, 'stdout', captured_output)

        # Act
        # Run the module as if it were executed directly from the command line.
        # `run_name='__main__'` ensures that `__name__` inside the module is set to '__main__'.
        # Changed module name from 'math_utils' to 'sample_utility'
        runpy.run_module('sample_utility', run_name='__main__')

        # Assert
        output = captured_output.getvalue()

        # Assert that the Fibonacci example output is present
        assert "--- Testing Fibonacci Function ---" in output
        assert "The Fibonacci sequence with 10 terms is: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]" in output

    def test_kill_mutant_triangle_area_print_guard(self, monkeypatch):
        """
        Kills Mutant 3: `if area is not None:` -> `if not (area is not None):`

        This test runs the `sample_utility` module directly and asserts that the
        expected triangle area example usage output is printed.
        It assumes `sample_utility.py` has an `if __name__ == "__main__":` block similar
        to the `math_utils.py` provided in the prompt.

        On original: The `if __name__ == "__main__":` block executes, `area` is
                     a valid float (not None), so the print statement for triangle
                     area runs. Test passes.

        On Mutant 3: The `if area is not None:` guard is inverted to `if not (area is not None):`.
                     Since `area` (e.g., `25.0`) is not `None`, `area is not None` is `True`.
                     Therefore, `not (area is not None)` evaluates to `False`.
                     The print statement for the triangle area will be skipped. Test fails.
        """
        # Arrange
        # Use io.StringIO to capture anything printed to sys.stdout
        captured_output = io.StringIO()
        monkeypatch.setattr(sys, 'stdout', captured_output)

        # Act
        # Run the module as if it were executed directly from the command line.
        # Changed module name from 'math_utils' to 'sample_utility'
        runpy.run_module('sample_utility', run_name='__main__')

        # Assert
        output = captured_output.getvalue()

        # Assert that the Triangle Area example output is present
        assert "--- Testing Triangle Area Function ---" in output
        assert "The area of a triangle with base 5 and height 10 is: 25.0" in output