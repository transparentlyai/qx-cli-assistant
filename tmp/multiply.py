import sys

def main():
    """
    Multiplies integer arguments passed via the command line.
    Non-integer arguments are skipped with a warning.
    """
    if len(sys.argv) < 2:
        print("Usage: python tmp/multiply.py <number1> [number2] ...")
        sys.exit(1)

    numbers = []
    for arg in sys.argv[1:]:
        try:
            numbers.append(int(arg))
        except ValueError:
            print(f"Warning: '{arg}' is not a valid integer and will be skipped.", file=sys.stderr)

    if not numbers:
        print("No valid numbers provided to multiply.")
        sys.exit(0)

    product = 1
    for num in numbers:
        product *= num
        
    print(f"Successfully multiplied {len(numbers)} numbers. The product is: {product}")

if __name__ == "__main__":
    main()
