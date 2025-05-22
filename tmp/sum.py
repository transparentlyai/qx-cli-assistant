import argparse
import sys
from typing import List, Tuple, Union, TextIO

def sum_numbers_from_list(numbers: List[Union[str, float]]) -> Tuple[float, List[str]]:
    """
    Calculates the sum of numeric values from a list.

    Args:
        numbers: A list of string or float arguments.

    Returns:
        A tuple containing:
            - The sum of the numbers that could be successfully converted.
            - A list of arguments that could not be converted to a float.
    """
    total: float = 0.0
    non_numeric_inputs: List[str] = []

    for item in numbers:
        try:
            num = float(item)
            total += num
        except ValueError:
            non_numeric_inputs.append(str(item))
    return total, non_numeric_inputs

def read_numbers_from_file(file_obj: TextIO) -> Tuple[List[str], List[str]]:
    """
    Reads numbers line by line from a file object.

    Args:
        file_obj: A file object opened for reading.

    Returns:
        A tuple containing:
            - A list of strings representing numbers read from the file.
            - A list of error messages for unreadable lines.
    """
    numbers_from_file: List[str] = []
    file_errors: List[str] = []
    for line_num, line in enumerate(file_obj, 1):
        try:
            stripped_line = line.strip()
            if stripped_line:
                numbers_from_file.append(stripped_line)
        except Exception as e:
            file_errors.append(f"Error reading line {line_num} from {file_obj.name}: {e}")
    return numbers_from_file, file_errors

def main():
    """
    Parses command-line arguments, sums the numeric ones,
    and prints the result or warnings.
    """
    parser = argparse.ArgumentParser(
        description="Calculate the sum of numbers provided as arguments or from files.",
        epilog="Example: python sum.py 1 2.5 3 foo --file numbers.txt"
    )
    parser.add_argument(
        'inputs',
        nargs='*',
        help='One or more numbers (integer or decimal) or file paths to sum up.'
    )
    parser.add_argument(
        '--file',
        dest='files',
        metavar='FILE',
        type=argparse.FileType('r'),
        action='append',
        help='Read numbers from the specified file(s), one number per line.'
    )

    parsed_args: argparse.Namespace = parser.parse_args()

    all_inputs_to_process: List[str] = []
    all_conversion_errors: List[str] = []

    if parsed_args.inputs:
        all_inputs_to_process.extend(parsed_args.inputs)

    if parsed_args.files:
        for file_obj in parsed_args.files:
            try:
                numbers_from_file, file_errors = read_numbers_from_file(file_obj)
                all_inputs_to_process.extend(numbers_from_file)
                all_conversion_errors.extend(file_errors)
            except IOError as e:
                all_conversion_errors.append(f"Cannot read file {file_obj.name}: {e}")
            finally:
                if file_obj and not file_obj.closed:
                    file_obj.close()

    if not all_inputs_to_process and not all_conversion_errors:
        if not (parsed_args.inputs or parsed_args.files):
            parser.print_help()
            sys.exit(0)

    total, non_numeric_inputs = sum_numbers_from_list(all_inputs_to_process)

    all_conversion_errors.extend(non_numeric_inputs)

    if all_conversion_errors:
        print("\n--- Warnings/Errors --- ", file=sys.stderr)
        for err in set(all_conversion_errors): # Use set to avoid duplicate error messages
            print(err, file=sys.stderr)
        print("-----------------------\n", file=sys.stderr)

    print(f"Total Sum: {total}")

if __name__ == "__main__":
    main()
