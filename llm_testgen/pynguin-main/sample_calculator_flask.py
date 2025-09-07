from flask import Flask, request, jsonify
import math

# Initialize the Flask application
app = Flask(__name__)

def calculator(a, b, operation):
    """
    Performs a calculation based on the operation.
    Returns a tuple: (result, error_message).
    """
    if operation == 'add':
        return a + b, None
    elif operation == 'sub':
        return a - b, None
    elif operation == 'mul':
        return a * b, None
    elif operation == 'div':
        if b == 0:
            return None, "Division by zero is not allowed."
        return a / b, None
    elif operation == 'mod':
        if b == 0:
            return None, "Modulus by zero is not allowed."
        return a % b, None
    elif operation == 'exp':
        return a ** b, None
    elif operation == 'floordiv':
        if b == 0:
            return None, "Floor division by zero is not allowed."
        return a // b, None
    elif operation == 'sqrt':
        if a < 0:
            return None, "Cannot calculate the square root of a negative number."
        return math.sqrt(a), None
    else:
        return None, "Invalid operation selected. Use: add, sub, mul, div, mod, exp, floordiv, sqrt."

@app.route('/calculate', methods=['GET'])
def calculate_api():
    """
    API endpoint to perform a calculation.
    Fetches parameters from the URL query string.
    """
    # --- Fetch parameters from the request ---
    try:
        operation = request.args.get('operation', type=str)
        a = request.args.get('a', type=float)
        
        # 'b' is not required for the 'sqrt' operation
        b = None
        if operation != 'sqrt':
            b = request.args.get('b', type=float)

        # --- Validate parameters ---
        if operation is None or a is None:
            raise ValueError("Missing required parameters.")
        if operation != 'sqrt' and b is None:
            raise ValueError("Parameter 'b' is required for this operation.")

    except (ValueError, TypeError):
        return jsonify({'error': "Invalid or missing parameters. Ensure 'a', 'b' (if needed), and 'operation' are provided correctly."}), 400

    # --- Perform the calculation ---
    result, error = calculator(a, b, operation)

    # --- Return the response ---
    if error:
        return jsonify({'error': error}), 400
    else:
        return jsonify({
            'operation': operation,
            'a': a,
            'b': b,
            'result': result
        })

if __name__ == '__main__':
    # Run the app in debug mode for development
    app.run(debug=True)

