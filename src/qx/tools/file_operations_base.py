# src/qx/tools/file_operations_base.py
from pathlib import Path
from typing import Optional

from qx.core.paths import USER_HOME_DIR, _find_project_root # Updated import


def is_path_allowed(
    resolved_path: Path, project_root: Optional[Path], user_home: Path
) -> bool:
    """
    Checks if a given resolved path is allowed for file operations.
    - If a project_root is defined, the path must be within the project_root.
    - If no project_root is defined, the path must be within the user_home.
    Access to '.Q' directory within the project is implicitly allowed if path is within project_root.
    """
    if project_root:
        # Check if the path is within the project root or project_root/.Q
        if project_root.resolve() in resolved_path.resolve().parents or project_root.resolve() == resolved_path.resolve() or project_root.resolve() == resolved_path.resolve().parent:
             # Further check: ensure it's not trying to go "above" project_root using ".." tricks
            if ".." in resolved_path.as_posix()[len(project_root.as_posix()):]: # Check relative part
                return False
            return True
        # Allow access to .Q directory specifically if it's directly under project_root
        if (project_root.resolve() / ".Q") in resolved_path.resolve().parents or (project_root.resolve() / ".Q") == resolved_path.resolve().parent or (project_root.resolve() / ".Q") == resolved_path.resolve():
            if ".." in resolved_path.as_posix()[len((project_root / ".Q").as_posix()):]:
                return False
            return True
        return False
    else:
        # If no project root, path must be within user's home directory
        if user_home.resolve() in resolved_path.resolve().parents or user_home.resolve() == resolved_path.resolve() or user_home.resolve() == resolved_path.resolve().parent:
            if ".." in resolved_path.as_posix()[len(user_home.as_posix()):]:
                return False
            return True
        return False

if __name__ == '__main__':
    # Basic tests for is_path_allowed
    # These tests are illustrative and might need a more robust setup to run universally
    print(f"Testing file_operations_base.py with USER_HOME_DIR: {USER_HOME_DIR}")

    # Simulate a project root
    current_dir = Path.cwd()
    simulated_project_root = current_dir / "test_project"
    simulated_dot_q = simulated_project_root / ".Q"

    # Test cases
    # 1. Path within project
    path1 = simulated_project_root / "file.txt"
    print(f"Path: {path1}, Allowed (with project_root): {is_path_allowed(path1, simulated_project_root, USER_HOME_DIR)}")

    # 2. Path within .Q in project
    path2 = simulated_dot_q / "q_file.txt"
    print(f"Path: {path2}, Allowed (with project_root): {is_path_allowed(path2, simulated_project_root, USER_HOME_DIR)}")

    # 3. Path outside project but in home (when project_root is None)
    path3 = USER_HOME_DIR / "some_home_file.txt"
    print(f"Path: {path3}, Allowed (no project_root): {is_path_allowed(path3, None, USER_HOME_DIR)}")

    # 4. Path outside project (when project_root is set)
    path4 = USER_HOME_DIR / "another_home_file.txt"
    # This test depends on whether simulated_project_root is inside USER_HOME_DIR or not.
    # If simulated_project_root is /some/path/test_project and USER_HOME_DIR is /home/user,
    # then path4 should be False if simulated_project_root is provided.
    print(f"Path: {path4}, Allowed (with project_root {simulated_project_root}): {is_path_allowed(path4, simulated_project_root, USER_HOME_DIR)}")


    # 5. Path completely outside (e.g. /etc/hosts)
    path5 = Path("/etc/hosts").resolve()
    print(f"Path: {path5}, Allowed (with project_root): {is_path_allowed(path5, simulated_project_root, USER_HOME_DIR)}")
    print(f"Path: {path5}, Allowed (no project_root): {is_path_allowed(path5, None, USER_HOME_DIR)}")

    # 6. Path traversal attempt
    path6 = simulated_project_root / ".." / "outside_project.txt"
    print(f"Path: {path6} (resolved: {path6.resolve()}), Allowed (with project_root): {is_path_allowed(path6.resolve(), simulated_project_root, USER_HOME_DIR)}")

    path7 = USER_HOME_DIR / ".." / "outside_home.txt"
    print(f"Path: {path7} (resolved: {path7.resolve()}), Allowed (no project_root): {is_path_allowed(path7.resolve(), None, USER_HOME_DIR)}")
