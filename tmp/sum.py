import sys

def sum_numbers(num1, num2):
    """Sums two numbers and returns the result."""
    return num1 + num2

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python sum.py <number1> <number2>")
        sys.exit(1)

    try:
        num1 = float(sys.argv[1])
        num2 = float(sys.argv[2])
        result = sum_numbers(num1, num2)
        print(f"The sum is: {result}")
    except ValueError:
        print("Error: Please provide valid numbers.")
        sys.exit(1)
