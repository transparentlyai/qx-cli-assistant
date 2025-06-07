import sys


def sum_params():
    """
    Calculates the sum of numeric command-line arguments.
    """
    # sys.argv[0] is the script name, so we skip it.
    args = sys.argv[1:]
    
    if not args:
        print("No numbers provided to sum.")
        return

    total = 0
    error_occurred = False
    for arg in args:
        try:
            # Convert each argument to a float to handle integers and decimals.
            total += float(arg)
        except ValueError:
            print(f"Error: Could not convert '{arg}' to a number. It will be ignored.", file=sys.stderr)
            error_occurred = True

    print(total)

    if error_occurred:
        sys.exit(1)

if __name__ == "__main__":
    sum_params()
