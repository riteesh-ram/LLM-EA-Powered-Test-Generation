import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
import runpy
import importlib
import io # Required to capture stdout for killer tests

# Add the tests/source directory to Python path to import the source module
current_dir = Path(__file__).parent
source_dir = current_dir.parent / "source"
sys.path.insert(0, str(source_dir))

import sample_utility

class TestSampleUtilityFunctions:
    """
    Comprehensive test suite for the sample_utility module, including
    tests for calculate_fibonacci, calculate_triangle_area, and killer tests
    for specific mutants.
    """

    # --- Tests for calculate_fibonacci function ---

    @pytest.mark.parametrize(
        "n, expected_sequence",
        [
            (1, [0]),
            (2, [0, 1]),
            (3, [0, 1, 1]),
            (5, [0, 1, 1, 2, 3]),
            (10, [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]),
        ],
        ids=[f"n={n}" for n, _ in [(1, [0]), (2, [0, 1]), (3, [0, 1, 1]), (5, [0, 1, 1, 2, 3]), (10, [0, 1, 1, 2, 3, 5, 8, 13, 21, 34])]]
    )
    def test_fibonacci_positive_integer_inputs(self, n, expected_sequence):
        """
        Test calculate_fibonacci with valid positive integer inputs.
        Verifies the correctness of the generated Fibonacci sequence.
        """
        # Arrange - inputs are provided by parametrize
        # Act
        result = sample_utility.calculate_fibonacci(n)
        # Assert
        assert result == expected_sequence

    @pytest.mark.parametrize(
        "n_invalid, expected_error_message",
        [
            (0, "Error: Input must be a positive integer."),
            (-5, "Error: Input must be a positive integer."),
            (1.5, "Error: Input must be a positive integer."),
            ("abc", "Error: Input must be a positive integer."),
            (None, "Error: Input must be a positive integer."),
            # --- New test cases from Pynguin analysis ---
            ([], "Error: Input must be a positive integer."),  # Empty list
            ([0, 1], "Error: Input must be a positive integer."), # Non-empty list
        ],
        ids=["n=0", "n=-5", "n=1.5_float", "n=string", "n=None", "n=empty_list", "n=list_fib_seq"]
    )
    def test_fibonacci_invalid_inputs_returns_empty_list_and_prints_error(self, n_invalid, expected_error_message, monkeypatch):
        """
        Test calculate_fibonacci with invalid inputs (non-positive integers, wrong types).
        Verifies that an empty list is returned and an error message is printed.
        Includes new cases for list types identified by Pynguin.
        """
        # Arrange
        mock_print = Mock()
        monkeypatch.setattr('builtins.print', mock_print)

        # Act
        result = sample_utility.calculate_fibonacci(n_invalid)

        # Assert
        assert result == []
        mock_print.assert_called_once_with(expected_error_message)

    # --- Tests for calculate_triangle_area function ---

    @pytest.mark.parametrize(
        "base, height, expected_area",
        [
            (10, 5, 25.0),
            (7.5, 4, 15.0),
            (0.1, 0.1, 0.005),
            (1, 1, 0.5),
            (100, 200, 10000.0),
            # --- New test cases from Pynguin analysis ---
            (True, True, 0.5), # Boolean inputs (True=1, False=0) are treated as numbers
        ],
        ids=["int_base_height", "float_base_int_height", "small_float", "unit_values", "large_values", "bool_inputs"]
    )
    def test_triangle_area_positive_numeric_inputs(self, base, height, expected_area):
        """
        Test calculate_triangle_area with valid positive numeric inputs (int, float, bool).
        Verifies the correct area calculation, handling floating point precision.
        Includes boolean inputs as valid numeric types.
        """
        # Arrange - inputs are provided by parametrize
        # Act
        result = sample_utility.calculate_triangle_area(base, height)
        # Assert
        # Use pytest.approx for floating-point comparisons to avoid precision issues
        assert result == pytest.approx(expected_area)

    @pytest.mark.parametrize(
        "base, height, expected_error_message",
        [
            (0, 5, "Error: Base and height must be positive values."),
            (10, 0, "Error: Base and height must be positive values."),
            (-5, 10, "Error: Base and height must be positive values."),
            (10, -5, "Error: Base and height must be positive values."),
            (0, 0, "Error: Base and height must be positive values."),
            (-1, -1, "Error: Base and height must be positive values."),
            # --- New test cases from Pynguin analysis ---
            (5, False, "Error: Base and height must be positive values."), # False (0) as height
            (False, 5, "Error: Base and height must be positive values."), # False (0) as base
        ],
        ids=["base=0", "height=0", "base_negative", "height_negative", "both_zero", "both_negative", "height=False", "base=False"]
    )
    def test_triangle_area_non_positive_numeric_inputs_returns_none_and_prints_error(self, base, height, expected_error_message, monkeypatch):
        """
        Test calculate_triangle_area with non-positive numeric inputs (including False).
        Verifies that None is returned and an error message is printed.
        """
        # Arrange
        mock_print = Mock()
        monkeypatch.setattr('builtins.print', mock_print)

        # Act
        result = sample_utility.calculate_triangle_area(base, height)

        # Assert
        assert result is None
        mock_print.assert_called_once_with(expected_error_message)

    @pytest.mark.parametrize(
        "base, height, expected_error_message",
        [
            ("a", 10, "Error: Base and height must be numbers."),
            (10, "b", "Error: Base and height must be numbers."),
            (None, 10, "Error: Base and height must be numbers."),
            (10, None, "Error: Base and height must be numbers."),
            ([1], 10, "Error: Base and height must be numbers."),
            (10, {"h": 10}, "Error: Base and height must be numbers."),
            # --- New test cases from Pynguin analysis ---
            (10, 1+2j, "Error: Base and height must be numbers."), # Complex number as height
            (1+2j, 10, "Error: Base and height must be numbers."), # Complex number as base
            (b'abc', 10, "Error: Base and height must be numbers."), # Bytes as base
            (10, b'abc', "Error: Base and height must be numbers."), # Bytes as height
        ],
        ids=["base_string", "height_string", "base_None", "height_None", "base_list", "height_dict",
             "height_complex", "base_complex", "base_bytes", "height_bytes"]
    )
    def test_triangle_area_non_numeric_inputs_returns_none_and_prints_error(self, base, height, expected_error_message, monkeypatch):
        """
        Test calculate_triangle_area with non-numeric inputs.
        Verifies that None is returned and an error message is printed.
        Includes new cases for complex numbers and bytes types identified by Pynguin.
        """
        # Arrange
        mock_print = Mock()
        monkeypatch.setattr('builtins.print', mock_print)

        # Act
        result = sample_utility.calculate_triangle_area(base, height)

        # Assert
        assert result is None
        mock_print.assert_called_once_with(expected_error_message)

    def test_triangle_area_mixed_valid_and_invalid_types(self, monkeypatch):
        """
        Test calculate_triangle_area with one valid and one invalid type.
        Ensures the type check correctly identifies the non-numeric input.
        """
        # Arrange
        mock_print = Mock()
        monkeypatch.setattr('builtins.print', mock_print)
        base = 5
        height = "invalid"
        expected_error_message = "Error: Base and height must be numbers."

        # Act
        result = sample_utility.calculate_triangle_area(base, height)

        # Assert
        assert result is None
        mock_print.assert_called_once_with(expected_error_message)

    def test_triangle_area_mixed_valid_type_and_non_positive_value(self, monkeypatch):
        """
        Test calculate_triangle_area with one valid type/value and one non-positive value.
        Ensures the positive value check correctly identifies the issue.
        """
        # Arrange
        mock_print = Mock()
        monkeypatch.setattr('builtins.print', mock_print)
        base = 5
        height = -10
        expected_error_message = "Error: Base and height must be positive values."

        # Act
        result = sample_utility.calculate_triangle_area(base, height)

        # Assert
        assert result is None
        mock_print.assert_called_once_with(expected_error_message)

    # --- Killer tests for surviving mutants ---

    def test_kill_mutant_main_block_execution_and_fibonacci_print_guard(self, monkeypatch):
        """
        Kills Mutant 1: `if __name__ == "__main__":` -> `if not (__name__ == '__main__'):`
        Kills Mutant 4: `if __name__ == "__main__":` -> `if __name__ != '__main__':`
        Kills Mutant 2: `if fib_sequence:` -> `if not fib_sequence:`

        This test runs the `sample_utility` module directly (simulating `python sample_utility.py`)
        and asserts that the expected Fibonacci example usage output is printed.

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
        runpy.run_module('sample_utility', run_name='__main__')

        # Assert
        output = captured_output.getvalue()

        # Assert that the Triangle Area example output is present
        assert "--- Testing Triangle Area Function ---" in output
        assert "The area of a triangle with base 5 and height 10 is: 25.0" in output