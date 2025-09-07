../source/import sample_maximum_sum_rectangle
import pytest

# It is good practice to put test classes into a Test_Class_Name convention.
# This helps pytest discover and organize the tests.
class TestMaxRectSum:
    
    # Test case with a simple matrix containing both positive and negative numbers.
    def test_with_positive_and_negative_numbers(self):
        """
        Test a standard matrix with a mix of positive and negative values.
        """
        mat = [
            [1, 2, -1, -4, -20],
            [-8, -3, 4, 2, 1],
            [3, 8, 10, 1, 3],
            [-4, -1, 1, 7, -6]
        ]
        assert sample_maximum_sum_rectangle.maxRectSum(mat) == 29

    # Test cases for matrices containing only positive numbers.
    def test_with_only_positive_numbers(self):
        """
        Test a matrix where all elements are positive. The largest sum should be
        the sum of the entire matrix.
        """
        mat = [
            [1, 2],
            [3, 4]
        ]
        assert sample_maximum_sum_rectangle.maxRectSum(mat) == 10

    # Test cases for matrices containing only negative numbers.
    def test_with_only_negative_numbers(self):
        """
        Test a matrix where all elements are negative. The largest sum should be
        the value of the single element closest to zero (the least negative value).
        """
        mat = [
            [-10, -5],
            [-3, -8]
        ]
        assert sample_maximum_sum_rectangle.maxRectSum(mat) == -3

    # Test case with a 1x1 matrix.
    def test_with_single_element_matrix(self):
        """
        Test a matrix containing only one element.
        """
        mat = [[5]]
        assert sample_maximum_sum_rectangle.maxRectSum(mat) == 5

    # Test case for a matrix with a single row.
    def test_with_single_row_matrix(self):
        """
        Test a matrix that consists of only one row.
        """
        mat = [[-2, 1, -3, 4, -1, 2, 1, -5, 4]]
        assert sample_maximum_sum_rectangle.maxRectSum(mat) == 6

    # Test case for a matrix with a single column.
    def test_with_single_column_matrix(self):
        """
        Test a matrix that consists of only one column.
        """
        mat = [
            [-2],
            [1],
            [-3],
            [4]
        ]
        assert sample_maximum_sum_rectangle.maxRectSum(mat) == 4

    # Test with an empty matrix.
    def test_with_empty_matrix(self):
        """
        Test for an empty matrix, which should handle the case gracefully.
        """
        mat = []
        with pytest.raises(IndexError):
            sample_maximum_sum_rectangle.maxRectSum(mat)
    
    # Test with a matrix containing an empty row.
    def test_with_matrix_containing_empty_row(self):
        """
        Test for a matrix containing an empty row. This should also raise an IndexError.
        """
        mat = [[]]
        with pytest.raises(IndexError):
            sample_maximum_sum_rectangle.maxRectSum(mat)

    # Parametrized tests for various edge cases and sizes.
    @pytest.mark.parametrize("mat, expected", [
        # Smallest possible matrix (1x1)
        ([[5]], 5),
        # Larger matrix with a mix of positive and negative numbers.
        ([
            [1, 2, -1, -4],
            [-8, -3, 4, 2],
            [3, 8, 10, 1]
        ], 22),
        # Matrix where the max sum is a single positive element.
        ([
            [-1, -2, -3],
            [-4, 5, -6],
            [-7, -8, -9]
        ], 5),
        # A matrix where all elements are zero.
        ([
            [0, 0],
            [0, 0]
        ], 0)
    ])
    def test_various_matrices(self, mat, expected):
        """
        Test various matrix sizes and compositions using parametrization.
        """
        assert sample_maximum_sum_rectangle.maxRectSum(mat) == expected