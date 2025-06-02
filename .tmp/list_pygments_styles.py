from pygments.styles import get_all_styles

print("Available Pygments Styles:")
for style in get_all_styles():
    print(f"- {style}")
