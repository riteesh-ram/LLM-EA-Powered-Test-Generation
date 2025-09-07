# math_utils.py
# A module containing functions for mathematical calculations.

def calculate_fibonacci(n):
    """
    Calculates the Fibonacci sequence up to the nth term.

    Args:
        n (int): The number of terms to generate in the sequence. 
                 Must be a positive integer.

    Returns:
        list: A list of integers representing the Fibonacci sequence.
              Returns an empty list if n is not a positive integer.
    """
    if not isinstance(n, int) or n <= 0:
        print("Error: Input must be a positive integer.")
        return []
    
    if n == 1:
        return [0]

    sequence = [0, 1]
    # Start the loop from 2 because the first two terms are already defined.
    while len(sequence) < n:
        next_value = sequence[-1] + sequence[-2]
        sequence.append(next_value)
        
    return sequence

def calculate_triangle_area(base, height):
    """
    Calculates the area of a triangle given its base and height.

    Args:
        base (float or int): The base of the triangle.
        height (float or int): The height of the triangle.

    Returns:
        float: The area of the triangle.
               Returns None if base or height are not positive numbers.
    """
    if not isinstance(base, (int, float)) or not isinstance(height, (int, float)):
        print("Error: Base and height must be numbers.")
        return None
        
    if base <= 0 or height <= 0:
        print("Error: Base and height must be positive values.")
        return None
        
    # Area of a triangle formula: 0.5 * base * height
    area = 0.5 * base * height
    return area

# --- Example Usage ---
if __name__ == "__main__":
    # This block of code will only run when the script is executed directly,
    # not when it's imported as a module.
    
    print("--- Testing Fibonacci Function ---")
    num_terms = 10
    fib_sequence = calculate_fibonacci(num_terms)
    if fib_sequence:
        print(f"The Fibonacci sequence with {num_terms} terms is: {fib_sequence}")

    print("\n--- Testing Triangle Area Function ---")
    tri_base = 5
    tri_height = 10
    area = calculate_triangle_area(tri_base, tri_height)
    if area is not None:
        print(f"The area of a triangle with base {tri_base} and height {tri_height} is: {area}")