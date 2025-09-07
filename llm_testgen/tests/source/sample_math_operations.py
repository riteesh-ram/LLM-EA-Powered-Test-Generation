"""
Sample math operations module for testing multiple function normalization.
Contains various mathematical operations with different complexity levels.
"""

import math
from typing import List, Union


class MathCalculator:
    """A calculator class with various mathematical operations."""
    
    def __init__(self, precision: int = 2):
        self.precision = precision
    
    def add_numbers(self, a: float, b: float) -> float:
        """Add two numbers with precision."""
        result = a + b
        return round(result, self.precision)
    
    def multiply_numbers(self, a: float, b: float) -> float:
        """Multiply two numbers with precision."""
        result = a * b
        return round(result, self.precision)


def calculate_area(shape: str, **kwargs) -> float:
    """
    Calculate area of different shapes.
    
    Args:
        shape: Type of shape ('circle', 'rectangle', 'triangle')
        **kwargs: Shape-specific parameters
        
    Returns:
        Area of the shape
        
    Raises:
        ValueError: If shape is not supported or missing parameters
    """
    if shape == 'circle':
        if 'radius' not in kwargs:
            raise ValueError("Radius required for circle")
        radius = kwargs['radius']
        if radius < 0:
            raise ValueError("Radius must be non-negative")
        return math.pi * radius ** 2
    
    elif shape == 'rectangle':
        if 'width' not in kwargs or 'height' not in kwargs:
            raise ValueError("Width and height required for rectangle")
        width, height = kwargs['width'], kwargs['height']
        if width < 0 or height < 0:
            raise ValueError("Width and height must be non-negative")
        return width * height
    
    elif shape == 'triangle':
        if 'base' not in kwargs or 'height' not in kwargs:
            raise ValueError("Base and height required for triangle")
        base, height = kwargs['base'], kwargs['height']
        if base < 0 or height < 0:
            raise ValueError("Base and height must be non-negative")
        return 0.5 * base * height
    
    else:
        raise ValueError(f"Unsupported shape: {shape}")


def find_statistics(numbers: List[Union[int, float]]) -> dict:
    """
    Calculate basic statistics for a list of numbers.
    
    Args:
        numbers: List of numbers
        
    Returns:
        Dictionary with mean, median, min, max
        
    Raises:
        ValueError: If list is empty or contains non-numeric values
    """
    if not numbers:
        raise ValueError("Cannot calculate statistics for empty list")
    
    # Validate all numbers
    for num in numbers:
        if not isinstance(num, (int, float)):
            raise ValueError(f"Non-numeric value found: {num}")
    
    # Calculate statistics
    sorted_nums = sorted(numbers)
    n = len(numbers)
    
    # Mean
    mean = sum(numbers) / n
    
    # Median
    if n % 2 == 0:
        median = (sorted_nums[n//2 - 1] + sorted_nums[n//2]) / 2
    else:
        median = sorted_nums[n//2]
    
    return {
        'mean': round(mean, 3),
        'median': median,
        'min': min(numbers),
        'max': max(numbers),
        'count': n
    }


def power_function(base: float, exponent: float) -> float:
    """
    Calculate base raised to the power of exponent.
    
    Args:
        base: Base number
        exponent: Exponent
        
    Returns:
        Result of base ** exponent
        
    Raises:
        ValueError: For invalid combinations (e.g., negative base with fractional exponent)
    """
    if base < 0 and not isinstance(exponent, int):
        raise ValueError("Cannot raise negative number to fractional power")
    
    if base == 0 and exponent < 0:
        raise ValueError("Cannot raise zero to negative power")
    
    try:
        result = base ** exponent
        return result
    except OverflowError:
        raise ValueError("Result too large to calculate")


# Function with complex nested logic
def process_number_sequence(sequence: List[int], operation: str = 'sum') -> Union[int, float]:
    """
    Process a sequence of numbers with various operations.
    
    Args:
        sequence: List of integers
        operation: Type of operation ('sum', 'product', 'average', 'factorial_sum')
        
    Returns:
        Result of the operation
    """
    if not sequence:
        return 0 if operation in ['sum', 'factorial_sum'] else 1 if operation == 'product' else None
    
    if operation == 'sum':
        return sum(sequence)
    
    elif operation == 'product':
        result = 1
        for num in sequence:
            result *= num
        return result
    
    elif operation == 'average':
        return sum(sequence) / len(sequence)
    
    elif operation == 'factorial_sum':
        def factorial(n):
            if n < 0:
                raise ValueError("Factorial not defined for negative numbers")
            if n == 0 or n == 1:
                return 1
            result = 1
            for i in range(2, n + 1):
                result *= i
            return result
        
        total = 0
        for num in sequence:
            if num < 0:
                continue  # Skip negative numbers
            if num > 10:  # Prevent large factorials
                raise ValueError(f"Factorial too large for {num}")
            total += factorial(num)
        return total
    
    else:
        raise ValueError(f"Unsupported operation: {operation}")


if __name__ == "__main__":
    # Test the functions
    print("Testing math operations...")
    
    # Test area calculation
    circle_area = calculate_area('circle', radius=5)
    print(f"Circle area: {circle_area}")
    
    # Test statistics
    stats = find_statistics([1, 2, 3, 4, 5])
    print(f"Statistics: {stats}")
    
    # Test power function
    power_result = power_function(2, 3)
    print(f"Power: {power_result}")
    
    # Test sequence processing
    seq_result = process_number_sequence([1, 2, 3, 4], 'factorial_sum')
    print(f"Factorial sum: {seq_result}")
    
    # Test calculator class
    calc = MathCalculator(3)
    sum_result = calc.add_numbers(1.23456, 2.34567)
    print(f"Calculator sum: {sum_result}")
