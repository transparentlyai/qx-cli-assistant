# src/qx/tools/file_operations_base.py
from pathlib import Path
from typing import Optional

from qx.core.paths import USER_HOME_DIR, _find_project_root # Updated import


def is_path_allowed(
    resolved_path: Path, project_root: Optional[Path], user_home: Path
) -> bool:
    """
    Checks if a given resolved path is allowed for file operations.
    A path is allowed if it is within the project_root (or its .Q subdirectory)
    OR if it is within the user_home directory.
    If project_root is defined, checks against it are performed first.
    """
    path_to_check = resolved_path.resolve() # Ensure we are working with absolute, normalized paths

    # 1. Check if within project_root or project_root/.Q (if project_root is defined)
    if project_root:
        project_root_abs = project_root.resolve()
        # Is path_to_check the project_root itself or a subdirectory/file within project_root?
        if path_to_check == project_root_abs or project_root_abs in path_to_check.parents:
            return True

        # Check for .Q directory within the project
        # Is path_to_check the .Q directory itself or a subdirectory/file within .Q?
        dot_q_path = (project_root_abs / ".Q").resolve()
        if path_to_check == dot_q_path or dot_q_path in path_to_check.parents:
            return True

    # 2. If not allowed via project_root (or if project_root was None), check if within user_home
    user_home_abs = user_home.resolve()
    # Is path_to_check the user_home itself or a subdirectory/file within user_home?
    if path_to_check == user_home_abs or user_home_abs in path_to_check.parents:
        return True

    # 3. If none of the above, the path is not allowed
    return False

if __name__ == '__main__':
    # Basic tests for is_path_allowed
    print(f"Testing file_operations_base.py with USER_HOME_DIR: {USER_HOME_DIR}")

    # Simulate a project root
    current_dir = Path.cwd() # e.g., /home/mauro/projects/qx
    # It's better if simulated_project_root is not the same as current_dir for some tests
    # Let's assume current_dir is /home/mauro/projects/qx
    # and USER_HOME_DIR is /home/mauro
    if USER_HOME_DIR in current_dir.parents or USER_HOME_DIR == current_dir:
        simulated_project_root = current_dir / "test_project_dir" # e.g. /home/mauro/projects/qx/test_project_dir
    else: # If current_dir is not under USER_HOME_DIR (e.g. /tmp/qx), place test_project_dir there
        simulated_project_root = current_dir / "test_project_dir"

    simulated_dot_q = simulated_project_root / ".Q"

    print(f"Using simulated_project_root: {simulated_project_root}")
    print(f"Using USER_HOME_DIR: {USER_HOME_DIR}")

    # Test cases
    # 1. Path within project
    path1 = simulated_project_root / "file.txt"
    print(f"1. Path: {path1}, Allowed (with project_root): {is_path_allowed(path1, simulated_project_root, USER_HOME_DIR)} (Expected: True)")

    # 2. Path within .Q in project
    path2 = simulated_dot_q / "q_file.txt"
    print(f"2. Path: {path2}, Allowed (with project_root): {is_path_allowed(path2, simulated_project_root, USER_HOME_DIR)} (Expected: True)")

    # 3. Path outside project but in home (when project_root is None)
    path3 = USER_HOME_DIR / "some_home_file.txt"
    print(f"3. Path: {path3}, Allowed (no project_root): {is_path_allowed(path3, None, USER_HOME_DIR)} (Expected: True)")

    # 4. Path outside project but in home (when project_root IS SET)
    path4 = USER_HOME_DIR / "another_home_file.txt"
    # This should now be TRUE with the new logic.
    print(f"4. Path: {path4}, Allowed (with project_root {simulated_project_root}): {is_path_allowed(path4, simulated_project_root, USER_HOME_DIR)} (Expected: True)")

    # 5. Path completely outside (e.g. /etc/hosts)
    path5 = Path("/etc/hosts").resolve()
    print(f"5. Path: {path5}, Allowed (with project_root): {is_path_allowed(path5, simulated_project_root, USER_HOME_DIR)} (Expected: False)")
    print(f"5. Path: {path5}, Allowed (no project_root): {is_path_allowed(path5, None, USER_HOME_DIR)} (Expected: False)")

    # 6. Path traversal attempt that resolves outside project but still in home
    #    e.g. project_root = /home/user/projects/test_project
    #    path6_raw = /home/user/projects/test_project/../some_other_file_in_projects.txt
    #    path6_resolved = /home/user/projects/some_other_file_in_projects.txt
    #    This should be TRUE if /home/user/projects/ is within USER_HOME_DIR.
    path6_raw = simulated_project_root / ".." / "some_other_file_in_home.txt"
    # Check if path6_raw.resolve() is actually within USER_HOME_DIR for the test to be meaningful
    expected_path6 = USER_HOME_DIR in path6_raw.resolve().parents or USER_HOME_DIR == path6_raw.resolve()
    print(f"6. Path: {path6_raw} (resolved: {path6_raw.resolve()}), Allowed (with project_root): {is_path_allowed(path6_raw.resolve(), simulated_project_root, USER_HOME_DIR)} (Expected: {expected_path6})")

    # 7. Path traversal attempt that resolves outside home
    path7_raw = USER_HOME_DIR / ".." / "outside_home.txt"
    print(f"7. Path: {path7_raw} (resolved: {path7_raw.resolve()}), Allowed (no project_root): {is_path_allowed(path7_raw.resolve(), None, USER_HOME_DIR)} (Expected: False)")
    
    # 8. Path that is exactly project_root
    print(f"8. Path: {simulated_project_root}, Allowed (with project_root): {is_path_allowed(simulated_project_root, simulated_project_root, USER_HOME_DIR)} (Expected: True)")

    # 9. Path that is exactly USER_HOME_DIR
    print(f"9. Path: {USER_HOME_DIR}, Allowed (no project_root): {is_path_allowed(USER_HOME_DIR, None, USER_HOME_DIR)} (Expected: True)")
    print(f"9. Path: {USER_HOME_DIR}, Allowed (with project_root {simulated_project_root}): {is_path_allowed(USER_HOME_DIR, simulated_project_root, USER_HOME_DIR)} (Expected: True)")

    # 10. Path that is a parent of project_root (e.g. project_root is /home/user/a/b/c, path is /home/user/a/b)
    #     This should be allowed if it's within USER_HOME_DIR.
    if simulated_project_root.parent != Path("/") and simulated_project_root.parent != USER_HOME_DIR.parent: # Avoid root or home's parent
        parent_of_project = simulated_project_root.parent
        expected_path10 = USER_HOME_DIR in parent_of_project.resolve().parents or USER_HOME_DIR == parent_of_project.resolve()
        print(f"10. Path: {parent_of_project}, Allowed (with project_root): {is_path_allowed(parent_of_project, simulated_project_root, USER_HOME_DIR)} (Expected: {expected_path10})")

    # 11. Path that is project_root/.Q
    print(f"11. Path: {simulated_dot_q}, Allowed (with project_root): {is_path_allowed(simulated_dot_q, simulated_project_root, USER_HOME_DIR)} (Expected: True)")