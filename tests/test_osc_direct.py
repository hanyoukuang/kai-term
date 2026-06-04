"""Test OSC features - results shown inside the terminal window.

Usage:
    uv run python tests/test_osc_direct.py
"""

import sys
from PySide6.QtWidgets import QApplication
from terminal.widget import TerminalWidget

ST = "\x1b\\"


def main():
    app = QApplication(sys.argv)

    widget = TerminalWidget(rows=24, cols=80, display_only=True)
    widget.resize(680, 500)

    # Connect signals to print to console
    widget.cwd_changed.connect(lambda d: print(f"[SIGNAL] cwd_changed: {d}"))
    widget.notification_received.connect(
        lambda t, m: print(f"[SIGNAL] notification: title='{t}' msg='{m}'"))
    widget.progress_changed.connect(
        lambda s, v: print(f"[SIGNAL] progress: state={s} value={v}%"))
    widget.title_changed.connect(lambda t: print(f"[SIGNAL] title: {t}"))

    def feed(text):
        widget.feed(text)

    # Clear screen and show header
    feed("\x1b[2J\x1b[H")
    feed("\x1b[1;36m=== OSC Feature Test ===\x1b[0m\n\n")

    # OSC 2: Title
    feed(f"\x1b]2;My Terminal{ST}")
    feed("OSC 0/2 Title: check window title bar\n")

    # OSC 7: CWD
    feed(f"\x1b]7;file:///home/user/project{ST}")
    feed("OSC 7 CWD: check console for cwd_changed signal\n")

    # OSC 8: Hyperlinks
    feed("OSC 8 Hyperlink: ")
    feed(f"\x1b]8;;https://github.com{ST}")
    feed("\x1b[4;34mGitHub (Ctrl+Click to open)\x1b[0m")
    feed(f"\x1b]8;;{ST}")
    feed("  |  ")
    feed(f"\x1b]8;;https://pypi.org{ST}")
    feed("\x1b[4;34mPyPI\x1b[0m")
    feed(f"\x1b]8;;{ST}")
    feed("\n")

    # OSC 9: Simple notification
    feed(f"\x1b]9;Build completed successfully!{ST}")
    feed("OSC 9 notification sent: 'Build completed successfully!'\n")

    # OSC 777: Structured notification
    feed(f"\x1b]777;notify;Test Status;All 42 tests passed{ST}")
    feed("OSC 777 notification sent: 'All 42 tests passed'\n")

    # OSC 9;4: Progress
    feed("OSC 9;4 Progress: ")
    for pct in [0, 25, 50, 75, 100]:
        feed(f"\x1b]9;4;1;{pct}{ST}")
        feed(f"\x1b[33m{pct}% \x1b[0m")
    feed(f"\x1b]9;4;0{ST}")
    feed("\n")

    # OSC 52: Clipboard
    import base64
    text = "Hello from pyqterminal OSC 52!"
    encoded = base64.b64encode(text.encode()).decode()
    feed(f"\x1b]52;c;{encoded}{ST}")
    feed(f"OSC 52 clipboard set: '{text}' (try Cmd+V)\n")

    feed("\n\x1b[1;32mAll OSC tests complete.\x1b[0m\n")
    feed("Check console output for [SIGNAL] messages.\n")

    widget.show()
    app.exec()


if __name__ == "__main__":
    main()
