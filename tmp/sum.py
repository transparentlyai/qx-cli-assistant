'''
import sys

def sum_all(*args):
    total = 0
    for arg in args:
        try:
            # Attempt to convert to float to handle integers and decimals
            num = float(arg)
            total += num
        except ValueError:
            print(f"Warning: Could not convert '{arg}' to a number. It will be ignored.", file=sys.stderr)
    return total

if __name__ == "__main__":
    # sys.argv[0] is the script name, arguments start from sys.argv[1]
    arguments = sys.argv[1:]
    if not arguments:
        print("Usage: python sum.py <num1> <num2> ... <numN>")
        sys.exit(1)
    
    result = sum_all(*arguments)
    print(result)
'''