import argparse
import sys
from typing import List, Tuple, Union

def calculate_sum(numbers_str: List[str]) -> Tuple[float, List[str]]:
    """
    Calculates the sum of numeric strings, reporting any invalid inputs.

    Args:
        numbers_str: A list of strings, each expected to represent a number.

    Returns:
        A tuple containing:
        - The total sum of valid numbers (float).
        - A list of strings that could not be converted to numbers.
    """
    total_sum: float = 0.0
    invalid_inputs: List[str] = []

    for arg in numbers_str:
        try:
            total_sum += float(arg)
        except ValueError:
            invalid_inputs.append(arg)
    
    return total_sum, invalid_inputs

def main():
    """
    Parses command-line arguments, sums numeric values, and prints the result.
    Handles non-numeric inputs gracefully.
    """
    parser = argparse.ArgumentParser(
        description="Sums all numeric command-line arguments.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        'numbers', 
        metavar='N', 
        type=str, 
        nargs='*', 
        help='''One or more numbers to be summed.
Example: python sum.py 10 20 30.5 "hello"'''
    )

    args = parser.parse_args()

    if not args.numbers:
        print("No numbers provided. Usage: python sum.py <number1> <number2> ...")
        sys.exit(0)

    total_sum, invalid_inputs = calculate_sum(args.numbers)

    if invalid_inputs:
        print(f"Warning: The following inputs were ignored due to being non-numeric: {', '.join(invalid_inputs)}", file=sys.stderr)
        print(f"Summation completed with warnings. Only valid numbers were summed.")
    
    print(f"The sum of the provided numbers is: {total_sum}")

if __name__ == "__main__":
    main()
