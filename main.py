"""Kai - A cross-platform terminal emulator with Rust backend and PySide6 frontend."""

import sys

from PySide6.QtWidgets import QApplication
from terminal.widget import TerminalWidget


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Kai")

    widget = TerminalWidget(rows=24, cols=80)
    widget.setWindowTitle("Kai")
    widget.resize(640, 480)
    widget.show()

    # Start the shell after the event loop is running
    widget.start_shell()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
