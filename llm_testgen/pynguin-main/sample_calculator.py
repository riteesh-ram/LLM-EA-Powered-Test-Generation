def calculator(a, b, operation):
    if operation == 'add':
        result = a + b
        print(f"Addition: {a} + {b} = {result}")

    elif operation == 'sub':
        result = a - b
        print(f"Subtraction: {a} - {b} = {result}")

    elif operation == 'mul':
        result = a * b
        print(f"Multiplication: {a} * {b} = {result}")

    elif operation == 'div':
        result = a / b
        print(f"Division: {a} / {b} = {result}")

    elif operation == 'mod':
        result = a % b
        print(f"Modulus: {a} % {b} = {result}")

    elif operation == 'exp':
        result = a ** b
        print(f"Exponentiation: {a} ** {b} = {result}")

    elif operation == 'floordiv':
        result = a // b
        print(f"Floor Division: {a} // {b} = {result}")

    else:
        print("Invalid operation selected.")

