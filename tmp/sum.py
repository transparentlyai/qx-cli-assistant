
import sys

def main():
    total = 0
    for arg in sys.argv[1:]:
        try:
            total += float(arg)
        except ValueError:
            print(f"Warning: Could not convert '{arg}' to a number. Skipping.")
    print(f"The sum is: {total}")

if __name__ == "__main__":
    main()
