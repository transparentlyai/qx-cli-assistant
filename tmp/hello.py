\
import argparse

def main():
    parser = argparse.ArgumentParser(description="Calculate the sum of two numbers.")
    parser.add_argument("num1", type=float, help="The first number.")
    parser.add_argument("num2", type=float, help="The second number.")
    
    args = parser.parse_args()
    
    result = args.num1 + args.num2
    print(result)

if __name__ == "__main__":
    main()
