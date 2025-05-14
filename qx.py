#!/usr/bin/env python3
# qx.py - Entry point for the QX application

import runpy
import os
import sys

if __name__ == "__main__":
    # Get the directory of this script (project root)
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Construct the path to the src directory
    src_path = os.path.join(project_root, "src")
    
    # Add src_path to the beginning of sys.path to ensure correct module resolution.
    # This allows 'import main' or 'from main import ...' to find src/main.py
    # if it's not already discoverable (e.g., if 'src' is not a package or project not installed).
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
        
    # Execute src/main.py as the main module.
    # runpy.run_module looks for 'main.py' (or a package 'main') in sys.path.
    # 'run_name="__main__"' ensures that the __name__ == "__main__" block
    # in src/main.py (if present) gets executed.
    # 'alter_sys=True' updates sys.argv and other sys attributes as if src/main.py
    # were the script directly invoked.
    try:
        runpy.run_module("main", run_name="__main__", alter_sys=True)
    except ModuleNotFoundError:
        print(f"Error: The module 'main' could not be found. Ensure 'src/main.py' exists.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred while trying to run 'src/main.py': {e}", file=sys.stderr)
        sys.exit(1)