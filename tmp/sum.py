import argparse
import sys
from typing import List, Tuple

def sum_all_numbers(args: List[str]) -> Tuple[float, List[str]]:
    """
    Calculates the sum of numeric values from a list of string arguments.

    Args:
        args: A list of string arguments, each expected to
              represent a number (integer or decimal).

    Returns:
        A tuple containing:
            - The sum of the numbers that could be successfully converted.
            - A list of arguments that could not be converted to a float.
    """
    total: float = 0.0
    non_numeric_inputs: List[str] = []

    for arg_str in args:
        try:
            num = float(arg_str)
            total += num
        except ValueError:
            non_numeric_inputs.append(arg_str)

    return total, non_numeric_inputs

def main():
    """
    Parses command-line arguments, sums the numeric ones,
    and prints the result or warnings.
    """
    parser = argparse.ArgumentParser(
        description="Calculate the sum of numbers provided as arguments.",
        epilog="Example: python sum.py 1 2.5 3 foo 4"
    )
    parser.add_argument(
        'numbers',
        nargs='+',
        help='One or more numbers (integer or decimal) to sum up.'
    )

    parsed_args: argparse.Namespace = parser.parse_args()

    if not parsed_args.numbers:
        # This case should ideally be handled by argparse (e.g. if nargs='*')
        # but with nargs='+', argparse exits if no arguments are given.
        # Keeping it for logical completeness if nargs was different.
        parser.print_help()
        sys.exit(1)

    total, non_numeric = sum_all_numbers(parsed_args.numbers)

    if non_numeric:
        error_message = (
            f"Warning: The following inputs could not be converted to numbers "
            f"and were ignored: {', '.join(non_numeric)}"
        )
        print(error_message, file=sys.stderr)

    print(total)

if __name__ == "__main__":
    main()
