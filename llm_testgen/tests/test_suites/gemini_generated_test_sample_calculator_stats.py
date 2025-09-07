import pytest
import sys
from pathlib import Path
import math
import statistics
from unittest.mock import Mock, patch, MagicMock

# Add the tests/source directory to Python path to import the source module
current_dir = Path(__file__).parent
source_dir = current_dir.parent / "source"
sys.path.insert(0, str(source_dir))

import sample_calculator_stats


# No mocking of 'print' is necessary as the functions under test
# (calculator, statistics_calculator) do not directly call 'print'.
# The example usage in __main__ does, but that block is not part of the functions' logic.

class TestCalculator:
    """
    Comprehensive test suite for the `calculator` function.
    Covers various arithmetic operations, edge cases, and error conditions.
    """

    @pytest.mark.parametrize(
        "a, operation, b, expected_result",
        [
            # Positive test cases for binary operations
            (10, 'add', 5, 15),
            (0, 'add', 0, 0),
            (-1, 'add', -2, -3),
            (10.5, 'add', 2.5, 13.0),

            (10, 'sub', 5, 5),
            (5, 'sub', 10, -5),
            (0, 'sub', 0, 0),
            (-1, 'sub', -2, 1),

            (2, 'mul', 3, 6),
            (-2, 'mul', 3, -6),
            (0, 'mul', 5, 0),
            (2.5, 'mul', 2, 5.0),

            (6, 'div', 3, 2.0),
            (10, 'div', 4, 2.5),
            (-6, 'div', 3, -2.0),
            (7.0, 'div', 2.0, 3.5),

            (7, 'mod', 3, 1),
            (10, 'mod', 5, 0),
            (-7, 'mod', 3, 2),  # Python's modulo for negative numbers
            (7.5, 'mod', 2.0, 1.5),

            (2, 'exp', 3, 8),
            (5, 'exp', 0, 1),
            (4, 'exp', 0.5, 2.0),  # Equivalent to sqrt(4)
            (2, 'exp', -1, 0.5),

            (7, 'floordiv', 3, 2),
            (10, 'floordiv', 4, 2),
            (-7, 'floordiv', 3, -3),  # Python's floor division for negative numbers
            (7.5, 'floordiv', 2.0, 3.0),
        ],
        ids=[
            "add_pos", "add_zero", "add_neg", "add_float",
            "sub_pos", "sub_neg_res", "sub_zero", "sub_neg",
            "mul_pos", "mul_neg", "mul_zero", "mul_float",
            "div_int", "div_float_res", "div_neg", "div_float",
            "mod_pos", "mod_zero_res", "mod_neg", "mod_float",
            "exp_pos", "exp_zero_power", "exp_fractional_power", "exp_neg_power",
            "floordiv_pos", "floordiv_float_res", "floordiv_neg", "floordiv_float",
        ]
    )
    def test_binary_operations_success(self, a, operation, b, expected_result):
        """
        Tests various binary arithmetic operations with valid inputs, including integers and floats.
        """
        result, error = sample_calculator_stats.calculator(a, operation, b)
        assert error is None
        assert math.isclose(result, expected_result)

    @pytest.mark.parametrize(
        "a, expected_result",
        [
            # Positive test cases for unary operation (sqrt)
            (4, 2.0),
            (0, 0.0),
            (9.0, 3.0),
            (16, 4.0),
            (2.25, 1.5),
        ],
        ids=["sqrt_pos_int", "sqrt_zero", "sqrt_pos_float", "sqrt_large_int", "sqrt_small_float"]
    )
    def test_sqrt_operation_success(self, a, expected_result):
        """
        Tests the square root operation with valid non-negative inputs.
        """
        result, error = sample_calculator_stats.calculator(a, 'sqrt')
        assert error is None
        assert math.isclose(result, expected_result)

    @pytest.mark.parametrize(
        "a, operation, b, expected_exception",
        [
            # Error cases for division by zero
            (10, 'div', 0, ZeroDivisionError),
            (10, 'mod', 0, ZeroDivisionError),
            (10, 'floordiv', 0, ZeroDivisionError),
        ],
        ids=["div_by_zero", "mod_by_zero", "floordiv_by_zero"]
    )
    def test_division_by_zero_errors(self, a, operation, b, expected_exception):
        """
        Tests that division, modulo, and floor division by zero raise ZeroDivisionError.
        """
        with pytest.raises(expected_exception):
            sample_calculator_stats.calculator(a, operation, b)

    def test_sqrt_negative_number_error(self):
        """
        Tests that square root of a negative number raises ValueError.
        """
        with pytest.raises(ValueError):
            sample_calculator_stats.calculator(-4, 'sqrt')

    @pytest.mark.parametrize(
        "a, operation",
        [
            # Error cases for binary operations missing 'b' (b defaults to None)
            (5, 'add'),
            (10, 'sub'),
            (2, 'mul'),
            (6, 'div'),
            (7, 'mod'),
            (2, 'exp'),
            (7, 'floordiv'),
        ],
        ids=[f"{op}_missing_b" for op in ['add', 'sub', 'mul', 'div', 'mod', 'exp', 'floordiv']]
    )
    def test_binary_operation_missing_b_raises_type_error(self, a, operation):
        """
        Tests that binary operations raise TypeError when 'b' is None (default),
        as arithmetic operations with None are not supported.
        """
        with pytest.raises(TypeError):
            sample_calculator_stats.calculator(a, operation)

    def test_invalid_operation(self):
        """
        Tests that an invalid operation string returns None and an "Invalid operation" error message.
        """
        result, error = sample_calculator_stats.calculator(1, 'invalid_op', 2)
        assert result is None
        assert error == "Invalid operation"

    def test_operation_with_non_numeric_input(self):
        """
        Tests that operations with non-numeric inputs raise TypeError,
        except for cases like int * str which Python handles as string repetition.
        """
        # This case correctly raises TypeError: can only concatenate str (not "int") to str
        with pytest.raises(TypeError):
            sample_calculator_stats.calculator("a", 'add', 5)
        
        # This case correctly raises TypeError: must be real number, not list
        with pytest.raises(TypeError):
            sample_calculator_stats.calculator([1], 'sqrt')

        # Test case for int * str, which results in string repetition, not TypeError
        result, error = sample_calculator_stats.calculator(10, 'mul', "b")
        assert error is None
        assert result == "bbbbbbbbbb"


class TestStatisticsCalculator:
    """
    Comprehensive test suite for the `statistics_calculator` function.
    Covers various statistical operations, edge cases, and error conditions.
    """

    @pytest.mark.parametrize(
        "numbers, operation, expected_result",
        [
            # Mean
            ([1, 2, 3], 'mean', 2.0),
            ([10, 20, 30, 40], 'mean', 25.0),
            ([0, 0, 0], 'mean', 0.0),
            ([-1, 0, 1], 'mean', 0.0),
            ([1.5, 2.5, 3.5], 'mean', 2.5),

            # Median
            ([1, 2, 3], 'median', 2.0),
            ([1, 2, 3, 4], 'median', 2.5),  # Even number of elements
            ([5, 1, 3], 'median', 3.0),  # Unsorted list
            ([10], 'median', 10.0),  # Single element
            ([-5, -1, -3], 'median', -3.0),

            # Variance (sample variance)
            ([1, 2, 3], 'variance', 1.0),
            ([10, 20, 30], 'variance', 100.0),
            ([5, 5, 5], 'variance', 0.0),  # All identical numbers

            # Standard Deviation (sample standard deviation)
            ([1, 2, 3], 'std_dev', 1.0),
            ([10, 20, 30], 'std_dev', 10.0),
            ([5, 5, 5], 'std_dev', 0.0),
        ],
        ids=[
            "mean_pos_int", "mean_large_int", "mean_zero", "mean_neg_int", "mean_float",
            "median_odd", "median_even", "median_unsorted", "median_single", "median_neg",
            "variance_pos", "variance_large", "variance_zero",
            "stddev_pos", "stddev_large", "stddev_zero",
        ]
    )
    def test_statistics_operations_success(self, numbers, operation, expected_result):
        """
        Tests various statistical operations with valid lists of numbers.
        Uses math.isclose for float comparisons.
        """
        result, error = sample_calculator_stats.statistics_calculator(numbers, operation)
        assert error is None
        assert math.isclose(result, expected_result)

    @pytest.mark.parametrize(
        "numbers, operation, expected_exception",
        [
            # Error cases for empty lists
            ([], 'mean', statistics.StatisticsError),
            ([], 'median', statistics.StatisticsError),
            ([], 'variance', statistics.StatisticsError),
            ([], 'std_dev', statistics.StatisticsError),

            # Error cases for single element list for variance/std_dev
            ([1], 'variance', statistics.StatisticsError),
            ([1], 'std_dev', statistics.StatisticsError),
        ],
        ids=[
            "mean_empty", "median_empty", "variance_empty", "stddev_empty",
            "variance_single_element", "stddev_single_element",
        ]
    )
    def test_statistics_empty_or_insufficient_data_errors(self, numbers, operation, expected_exception):
        """
        Tests that statistical operations raise StatisticsError for empty lists
        or lists with insufficient data (e.g., single element for variance/std_dev).
        """
        with pytest.raises(expected_exception):
            sample_calculator_stats.statistics_calculator(numbers, operation)

    @pytest.mark.parametrize(
        "numbers, operation",
        [
            # Error cases for non-numeric data in the list
            ([1, 'a', 3], 'mean'),
            ([1, None, 3], 'median'),
            ([1, 2, {}], 'variance'),
            ([1, 2, []], 'std_dev'),
        ],
        ids=["non_numeric_mean", "non_numeric_median", "non_numeric_variance", "non_numeric_stddev"]
    )
    def test_statistics_non_numeric_data_raises_type_error(self, numbers, operation):
        """
        Tests that statistical operations raise TypeError when the input list contains non-numeric data.
        """
        with pytest.raises(TypeError):
            sample_calculator_stats.statistics_calculator(numbers, operation)

    def test_invalid_statistics_operation(self):
        """
        Tests that an invalid statistics operation string returns None and an "Invalid operation" error message.
        """
        result, error = sample_calculator_stats.statistics_calculator([1, 2, 3], 'invalid_stat_op')
        assert result is None
        assert error == "Invalid operation"

    def test_statistics_with_large_numbers(self):
        """
        Tests statistics calculator with large numbers to ensure correct handling.
        """
        numbers = [10**5, 2 * 10**5, 3 * 10**5]
        result, error = sample_calculator_stats.statistics_calculator(numbers, 'mean')
        assert error is None
        assert math.isclose(result, 2 * 10**5)

        result, error = sample_calculator_stats.statistics_calculator(numbers, 'std_dev')
        assert error is None
        # Expected std_dev for [100000, 200000, 300000] is 100000.0 (sample std dev)
        assert math.isclose(result, 100000.0)

    def test_statistics_with_mixed_positive_negative_numbers(self):
        """
        Tests statistics calculator with a mix of positive and negative numbers.
        """
        numbers = [-10, 0, 10, 20]
        result, error = sample_calculator_stats.statistics_calculator(numbers, 'mean')
        assert error is None
        assert math.isclose(result, 5.0) # (-10 + 0 + 10 + 20) / 4 = 20 / 4 = 5

        result, error = sample_calculator_stats.statistics_calculator(numbers, 'median')
        assert error is None
        assert math.isclose(result, 5.0) # (0 + 10) / 2 = 5