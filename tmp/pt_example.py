from prompt_toolkit import prompt

def main():
    text = prompt("Enter your name: ")
    print(f"Hello, {text}!")

if __name__ == "__main__":
    main()
