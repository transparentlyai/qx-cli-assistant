import importlib
import inspect
import logging
import pkgutil
from pathlib import Path
from typing import Callable, List, Any

logger = logging.getLogger(__name__)

class PluginManager:
    """
    Manages the discovery and loading of QX plugins.
    Plugins are expected to be PydanticAI-compatible tools (functions).
    """

    def __init__(self):
        pass

    def load_plugins(self, plugin_package_path: str = "qx.plugins") -> List[Callable[..., Any]]:
        """
        Scans the specified plugin package directory for modules, imports them,
        and collects PydanticAI-compatible tool functions.

        Args:
            plugin_package_path: The dot-separated path to the plugins package
                                 (e.g., "qx.plugins").

        Returns:
            A list of callable tool functions.
        """
        loaded_tools: List[Callable[..., Any]] = []
        
        try:
            package = importlib.import_module(plugin_package_path)
        except ImportError:
            logger.error(f"Plugin package '{plugin_package_path}' not found.")
            return loaded_tools

        plugin_module_path = Path(package.__file__).parent

        for _, module_name, _ in pkgutil.iter_modules([str(plugin_module_path)]):
            if module_name.endswith("_plugin"): # Convention: plugins are in *_plugin.py files
                try:
                    full_module_name = f"{plugin_package_path}.{module_name}"
                    plugin_module = importlib.import_module(full_module_name)
                    
                    # Inspect module for functions intended as tools
                    # Convention: tool functions are named like '*_tool'
                    for name, func in inspect.getmembers(plugin_module, inspect.isfunction):
                        if name.endswith("_tool"):
                            logger.info(f"Discovered tool: '{name}' in module '{full_module_name}'")
                            loaded_tools.append(func)
                except ImportError as e:
                    logger.error(f"Failed to import plugin module '{module_name}': {e}", exc_info=True)
                except Exception as e:
                    logger.error(f"Error processing plugin module '{module_name}': {e}", exc_info=True)
        
        if not loaded_tools:
            logger.warning(f"No plugins found in '{plugin_package_path}'.")
            
        return loaded_tools

if __name__ == "__main__":
    # This is a basic test/demonstration.
    # To run this, you'd need to have some dummy plugin files in a qx/plugins directory.
    
    # Create dummy structure for testing if it doesn't exist
    # (This part is for local testing of this script, not part of QX runtime)
    from qx.core.paths import PROJECT_ROOT_PATH
    
    # Assuming PROJECT_ROOT_PATH is correctly set to the root of your qx project
    # e.g., /home/mauro/projects/qx
    
    # Construct the path to src/qx/plugins
    plugins_dir = PROJECT_ROOT_PATH / "src" / "qx" / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)
    (plugins_dir / "__init__.py").touch(exist_ok=True) # Ensure it's a package

    # Dummy plugin 1
    dummy_plugin_1_content = """
from pydantic import BaseModel, Field
def dummy_read_tool(path: str) -> str:
    '''Reads a dummy file.'''
    return f"Content of {path}"
"""
    (plugins_dir / "dummy_read_plugin.py").write_text(dummy_plugin_1_content)

    # Dummy plugin 2
    dummy_plugin_2_content = """
def dummy_write_tool(path: str, content: str) -> str:
    '''Writes dummy content.'''
    return f"Wrote to {path}"

def another_utility_func(): # Should not be picked up
    pass
"""
    (plugins_dir / "dummy_write_plugin.py").write_text(dummy_plugin_2_content)
    
    # Dummy plugin 3 (non-tool function)
    dummy_plugin_3_content = """
def not_a_tool_function():
    return "This is not a tool"
"""
    (plugins_dir / "dummy_other_plugin.py").write_text(dummy_plugin_3_content)


    print("Testing PluginManager...")
    logging.basicConfig(level=logging.INFO)
    manager = PluginManager()
    # We need to ensure qx.plugins is in sys.path or discoverable
    # For this test, assuming the script is run from a context where qx.plugins is importable
    
    # Adjust path for importlib if necessary, or ensure PYTHONPATH is set
    # For direct execution, if qx is in the parent of src, this might work:
    import sys
    sys.path.insert(0, str(PROJECT_ROOT_PATH / "src")) # Add src to path for qx.plugins
    
    discovered_tools = manager.load_plugins() # Default path is "qx.plugins"
    
    print(f"\nDiscovered {len(discovered_tools)} tools:")
    for tool_func in discovered_tools:
        print(f"  - {tool_func.__name__} (from module: {tool_func.__module__})")
        if hasattr(tool_func, "__doc__") and tool_func.__doc__:
             print(f"    Doc: {tool_func.__doc__.strip()}")

    # Expected output:
    # Discovered 2 tools:
    #   - dummy_read_tool (from module: qx.plugins.dummy_read_plugin)
    #     Doc: Reads a dummy file.
    #   - dummy_write_tool (from module: qx.plugins.dummy_write_plugin)
    #     Doc: Writes dummy content.

    # Cleanup dummy files (optional, for cleanliness)
    # (plugins_dir / "dummy_read_plugin.py").unlink(missing_ok=True)
    # (plugins_dir / "dummy_write_plugin.py").unlink(missing_ok=True)
    # (plugins_dir / "dummy_other_plugin.py").unlink(missing_ok=True)
    # if not any(plugins_dir.iterdir()): # if __init__.py is the only thing left
    #     (plugins_dir / "__init__.py").unlink(missing_ok=True)
    #     try:
    #         plugins_dir.rmdir()
    #     except OSError:
    #         pass # might not be empty if other files were created
    print("\nPluginManager test finished.")
