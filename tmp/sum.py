import sys
from typing import List

def sum_all(*args: str) -> float:
    """
    Calculates the sum of numeric values provided as string arguments.

    Args:
        *args: A variable number of string arguments, each expected to
               represent a number (integer or decimal).

    Returns:
        The sum of the numbers that could be successfully converted.
        Prints a warning to stderr for any argument that cannot be
        converted to a float.
    """
    total: float = 0.0
    non_numeric_inputs: List[str] = []

    for arg_str in args:
        try:
            num = float(arg_str)
            total += num
        except ValueError:
            non_numeric_inputs.append(arg_str)

    if non_numeric_inputs:
        error_message = (
            f"Warning: The following inputs could not be converted to numbers "
            f"and were ignored: {', '.join(non_numeric_inputs)}"
        )
        print(error_message, file=sys.stderr)

    return total

if __name__ == "__main__":
    arguments: List[str] = sys.argv[1:]
    if not arguments:
        print("Usage: python sum.py <num1> <num2> ... <numN>")
        print("Example: python sum.py 1 2.5 3")
        sys.exit(1)

    result: float = sum_all(*arguments)
    print(result)
