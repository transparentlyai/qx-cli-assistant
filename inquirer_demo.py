import inquirer  # type: ignore
from inquirer.themes import GreenPassion  # type: ignore

# Define the questions
questions = [
    inquirer.Text("name", message="What's your name?"),
    inquirer.Password("password", message="What's your password?"),
    inquirer.Confirm("correct", message="Is this correct?", default=True),
    inquirer.List(
        "framework",
        message="What web framework do you use?",
        choices=["Django", "Flask", "Pyramid", "Tornado"],
    ),
    inquirer.Checkbox(
        "interests",
        message="What are you interested in?",
        choices=["Reading", "Coding", "Sports", "Music"],
    ),
    inquirer.List(
        "theme",
        message="What theme would you like to use?",
        choices=["GreenPassion", "Default", "Blue"],
    ),
]

# Prompt the user for answers
answers = inquirer.prompt(questions, theme=GreenPassion())

# Print the answers
print("Answers:")
if answers:
    for key, value in answers.items():
        print(f"{key}: {value}")

    # Apply the selected theme
    if answers["theme"] == "GreenPassion":
        theme = GreenPassion()
    elif answers["theme"] == "Blue":
        # A simple blue theme
        theme = {
            "Question": {
                "mark_color": "blue",
                "brackets_color": "bright_blue",
            },
            "List": {"selection_color": "bright_blue", "selection_cursor": ">"},
        }
    else:
        theme = {}

    # Re-prompt with the selected theme to show the change
    print("\n--- Now with your selected theme! ---")
    inquirer.prompt(questions, theme=theme)
