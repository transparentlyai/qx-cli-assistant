
import sys

def sum_params():
    total = 0
    for arg in sys.argv[1:]:
        try:
            total += int(arg)
        except ValueError:
            print(f"Error: Could not convert '{arg}' to an integer.")
            sys.exit(1)
    print(f"The sum is: {total}")

if __name__ == "__main__":
    sum_params()
