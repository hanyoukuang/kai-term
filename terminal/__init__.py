"""pyqterminal - A cross-platform terminal emulator with Rust backend and PySide6 frontend."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("pyqterminal")
except PackageNotFoundError:
    __version__ = "0.0.0"

from terminal.input_handler import InputHandler
from terminal.widget import TerminalWidget

__all__ = ["TerminalWidget", "InputHandler", "__version__"]
