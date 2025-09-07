import math
import statistics


def calculator(a, operation, b=None):
    if operation == 'add':
        return (a + b, None)
    elif operation == 'sub':
        return a - b, None
    elif operation == 'mul':
        return a * b, None
    elif operation == 'div':
        return a / b, None
    elif operation == 'mod':
        return a % b, None
    elif operation == 'exp':
        return a ** b, None
    elif operation == 'floordiv':
        return a // b, None
    elif operation == 'sqrt':
        return math.sqrt(a), None
    else:
        return None, "Invalid operation"


def statistics_calculator(numbers, operation):
    if operation == 'mean':
        return statistics.mean(numbers), None
    elif operation == 'median':
        return statistics.median(numbers), None
    elif operation == 'variance':
        return statistics.variance(numbers), None
    elif operation == 'std_dev':
        return statistics.stdev(numbers), None
    else:
        return None, "Invalid operation"


# Example usage
if __name__ == '__main__':
    # Arithmetic examples
    result, error = calculator(10, 'add', 5)
    print(f"10 + 5 = {result}")  # Output: 10 + 5 = 15
    
    result, error = calculator(16, 'sqrt')
    print(f"√16 = {result}")     # Output: √16 = 4.0
    
    # Note: This will now raise ZeroDivisionError instead of returning error message
    # result, error = calculator(10, 'div', 0)
    
    # Statistics examples
    data = [1, 2, 3, 4, 5]
    result, error = statistics_calculator(data, 'mean')
    print(f"Mean = {result}")    # Output: Mean = 3.0
    
    result, error = statistics_calculator(data, 'std_dev')
    print(f"Std Dev = {result}") # Output: Std Dev = 1.58...
