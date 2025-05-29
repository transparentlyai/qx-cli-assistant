import importlib
import inspect
import logging
import pkgutil
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

from pydantic import (  # Import BaseModel and Field for schema extraction
    BaseModel,
    Field,
)

logger = logging.getLogger(__name__)


class PluginManager:
    """
    Manages the discovery and loading of QX plugins.
    Plugins are expected to be functions with Pydantic BaseModel input arguments.
    """

    def __init__(self):
        pass

    def load_plugins(
        self, plugin_package_path: str = "qx.plugins"
    ) -> List[Tuple[Callable[..., Any], Dict[str, Any], Type[BaseModel]]]:
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
        loaded_tools: List[
            Tuple[Callable[..., Any], Dict[str, Any], Type[BaseModel]]
        ] = []

        try:
            package = importlib.import_module(plugin_package_path)
        except ImportError:
            logger.error(f"Plugin package '{plugin_package_path}' not found.")
            return loaded_tools

        plugin_module_path = Path(package.__file__).parent

        for _, module_name, _ in pkgutil.iter_modules([str(plugin_module_path)]):
            if module_name.endswith(
                "_plugin"
            ):  # Convention: plugins are in *_plugin.py files
                try:
                    full_module_name = f"{plugin_package_path}.{module_name}"
                    plugin_module = importlib.import_module(full_module_name)

                    # Inspect module for functions intended as tools
                    # Convention: tool functions are named like '*_tool'
                    for name, func in inspect.getmembers(
                        plugin_module, inspect.isfunction
                    ):
                        if name.endswith("_tool"):
                            # Extract schema from the tool function's signature
                            signature = inspect.signature(func)
                            parameters = signature.parameters

                            # Look for a parameter annotated with a Pydantic BaseModel
                            input_model_class: Optional[Type[BaseModel]] = None
                            for param_name, param in parameters.items():
                                if param_name == "console":  # Skip console parameter
                                    continue
                                if inspect.isclass(param.annotation) and issubclass(
                                    param.annotation, BaseModel
                                ):
                                    input_model_class = param.annotation
                                    break

                            if input_model_class is None:
                                logger.warning(
                                    f"Tool '{name}' in module '{full_module_name}' does not have a Pydantic BaseModel input argument. Skipping."
                                )
                                continue

                            # Construct OpenAI-compatible tool schema
                            tool_name = func.__name__
                            tool_description = inspect.getdoc(func) or ""
                            tool_parameters_schema = (
                                input_model_class.model_json_schema()
                            )

                            openai_tool_schema = {
                                "name": tool_name,
                                "description": tool_description,
                                "parameters": tool_parameters_schema,
                            }

                            logger.info(
                                f"Discovered tool: '{name}' in module '{full_module_name}' with schema."
                            )
                            loaded_tools.append(
                                (func, openai_tool_schema, input_model_class)
                            )

                except ImportError as e:
                    logger.error(
                        f"Failed to import plugin module '{module_name}': {e}",
                        exc_info=True,
                    )
                except Exception as e:
                    logger.error(
                        f"Error processing plugin module '{module_name}': {e}",
                        exc_info=True,
                    )

        if not loaded_tools:
            logger.warning(f"No plugins found in '{plugin_package_path}'.")

        return loaded_tools

