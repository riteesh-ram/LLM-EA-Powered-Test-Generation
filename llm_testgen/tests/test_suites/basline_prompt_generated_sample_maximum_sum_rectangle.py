import unittest
from sample_maximum_sum_rectangle import maxRectSum

class TestMaxRectSum(unittest.TestCase):
    
    def test_example_matrix(self):
        """Test with the provided example matrix."""
        mat = [
            [1, 2, -1, -4, -20],
            [-8, -3, 4, 2, 1],
            [3, 8, 10, 1, 3],
            [-4, -1, 1, 7, -6]
        ]
        self.assertEqual(maxRectSum(mat), 29)

    def test_single_positive_number(self):
        """Test a matrix with a single positive number."""
        mat = [[5]]
        self.assertEqual(maxRectSum(mat), 5)

    def test_single_negative_number(self):
        """Test a matrix with a single negative number."""
        mat = [[-10]]
        self.assertEqual(maxRectSum(mat), -10)
        
    def test_all_positive_numbers(self):
        """Test a matrix with all positive numbers."""
        mat = [
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9]
        ]
        self.assertEqual(maxRectSum(mat), 45)

    def test_all_negative_numbers(self):
        """Test a matrix with all negative numbers."""
        mat = [
            [-1, -2, -3],
            [-4, -5, -6],
            [-7, -8, -9]
        ]
        self.assertEqual(maxRectSum(mat), -1)
    
    def test_mixed_positive_and_negative(self):
        """Test with a mixed matrix."""
        mat = [
            [-1, 2],
            [3, -4]
        ]
        self.assertEqual(maxRectSum(mat), 3)

    def test_zero_in_matrix(self):
        """Test a matrix with zeros."""
        mat = [
            [0, 0, 0],
            [0, 1, 0],
            [0, 0, 0]
        ]
        self.assertEqual(maxRectSum(mat), 1)

    def test_large_matrix(self):
        """Test with a larger matrix to ensure efficiency (though the provided code has high time complexity)."""
        mat = [[1 for _ in range(50)] for _ in range(50)]
        self.assertEqual(maxRectSum(mat), 2500)

if __name__ == '__main__':
    unittest.main()