# src/qx/tools/read_file.py

from typing import Union

def read_file(file_path: str) -> Union[str, None]:
    """
    Reads the content of a file and returns it as a string.

    Args:
        file_path: The path to the file.

    Returns:
        The content of the file as a string, or None if an error occurs.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except FileNotFoundError:
        # Consider logging this error or raising a custom exception
        print(f"Error: File not found at path {file_path}")
        return None
    except IOError as e:
        # Consider logging this error or raising a custom exception
        print(f"Error reading file at path {file_path}: {e}")
        return None
