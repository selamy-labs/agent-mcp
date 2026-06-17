"""datakit: deterministic data utilities exposed as an MCP server."""

from . import core
from .core import DataKitError

__all__ = ["core", "DataKitError", "__version__"]

__version__ = "0.1.0"
