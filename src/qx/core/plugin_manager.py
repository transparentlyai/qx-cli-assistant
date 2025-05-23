import importlib
import inspect
import logging
import pkgutil
from pathlib import Path
from typing import Callable, List, Any, Dict, Tuple, Type, Optional

from pydantic import BaseModel, Field # Import BaseModel and Field for schema extraction

logger = logging.getLogger(__name__)

class PluginManager:
    """
    Manages the discovery and loading of QX plugins.
    Plugins are expected to be functions with Pydantic BaseModel input arguments.
    """

    def __init__(self):
        pass

    def load_plugins(self, plugin_package_path: str = "qx.plugins") -> List[Tuple[Callable[..., Any], Dict[str, Any], Type[BaseModel]]]:
        """
        Scans the specified plugin package directory for modules, imports them,
        and collects QX-compatible tool functions along with their OpenAI-compatible schemas
        and their Pydantic input model classes.

        Args:
            plugin_package_path: The dot-separated path to the plugins package
                                 (e.g., "qx.plugins").

        Returns:
            A list of tuples, where each tuple contains:
            (callable_tool_function, openai_tool_json_schema_dict, pydantic_input_model_class).
        """
        loaded_tools: List[Tuple[Callable[..., Any], Dict[str, Any], Type[BaseModel]]] = []
        
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
                            # Extract schema from the tool function's signature
                            signature = inspect.signature(func)
                            parameters = signature.parameters

                            # Look for a parameter annotated with a Pydantic BaseModel
                            input_model_class: Optional[Type[BaseModel]] = None
                            for param_name, param in parameters.items():
                                if param_name == "console": # Skip console parameter
                                    continue
                                if inspect.isclass(param.annotation) and issubclass(param.annotation, BaseModel):
                                    input_model_class = param.annotation
                                    break
                            
                            if input_model_class is None:
                                logger.warning(f"Tool '{name}' in module '{full_module_name}' does not have a Pydantic BaseModel input argument. Skipping.")
                                continue

                            # Construct OpenAI-compatible tool schema
                            tool_name = func.__name__
                            tool_description = inspect.getdoc(func) or ""
                            tool_parameters_schema = input_model_class.model_json_schema()

                            openai_tool_schema = {
                                "name": tool_name,
                                "description": tool_description,
                                "parameters": tool_parameters_schema,
                            }
                            
                            logger.info(f"Discovered tool: '{name}' in module '{full_module_name}' with schema.")
                            loaded_tools.append((func, openai_tool_schema, input_model_class))

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
    from qx.core.paths import USER_HOME_DIR # Using USER_HOME_DIR for a safe temp location
    
    # Construct a temporary plugins directory for testing
    temp_test_dir = USER_HOME_DIR / ".qx_test_plugins"
    plugins_dir = temp_test_dir / "qx" / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)
    (plugins_dir / "__init__.py").touch(exist_ok=True) # Ensure it's a package

    # Dummy plugin 1
    dummy_plugin_1_content = """
from pydantic import BaseModel, Field
from rich.console import Console as RichConsole

class DummyReadInput(BaseModel):
    path: str = Field(..., description="Path to read.")

class DummyReadOutput(BaseModel):
    content: str

def dummy_read_tool(console: RichConsole, args: DummyReadInput) -> DummyReadOutput:
    '''Reads a dummy file content.'''
    console.print(f"Dummy reading {args.path}")
    return DummyReadOutput(content=f"Content of {args.path}")
"""
    (plugins_dir / "dummy_read_plugin.py").write_text(dummy_plugin_1_content)

    # Dummy plugin 2
    dummy_plugin_2_content = """
from pydantic import BaseModel, Field
from rich.console import Console as RichConsole

class DummyWriteInput(BaseModel):
    path: str = Field(..., description="Path to write.")
    data: str = Field(..., description="Data to write.")

def dummy_write_tool(console: RichConsole, args: DummyWriteInput) -> str:
    '''Writes dummy content to a file.'''
    console.print(f"Dummy writing to {args.path}")
    return f"Wrote '{args.data}' to {args.path}"

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

    # Dummy plugin 4 (tool without Pydantic input)
    dummy_plugin_4_content = """
from rich.console import Console as RichConsole
def no_pydantic_tool(console: RichConsole, some_arg: str) -> str:
    '''A tool without Pydantic input.'''
    return f"Processed {some_arg}"
"""
    (plugins_dir / "no_pydantic_plugin.py").write_text(dummy_plugin_4_content)


    print("Testing PluginManager...")
    logging.basicConfig(level=logging.INFO)
    manager = PluginManager()
    
    # Add the temporary test directory to sys.path so importlib can find 'qx.plugins'
    import sys
    sys.path.insert(0, str(temp_test_dir))
    
    discovered_tools = manager.load_plugins()
    
    print(f"\nDiscovered {len(discovered_tools)} tools:")
    for tool_func, tool_schema, input_model_class in discovered_tools:
        print(f"  - {tool_func.__name__} (from module: {tool_func.__module__})")
        print(f"    Schema: {tool_schema}")
        print(f"    Input Model Class: {input_model_class.__name__}")
        if hasattr(tool_func, "__doc__") and tool_func.__doc__:
             print(f"    Doc: {tool_func.__doc__.strip()}")

    # Expected output should include dummy_read_tool and dummy_write_tool with their schemas.
    # no_pydantic_tool should be skipped with a warning.

    # Cleanup dummy files
    import shutil
    if temp_test_dir.exists():
        shutil.rmtree(temp_test_dir)
    
    # Remove the added path from sys.path
    sys.path.remove(str(temp_test_dir))

    print("\nPluginManager test finished.")