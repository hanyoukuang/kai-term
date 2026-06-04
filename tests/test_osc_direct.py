"""Test OSC features directly with TerminalWidget (no PTY needed).

Usage:
    uv run python tests/test_osc_direct.py
"""

import sys
from PySide6.QtWidgets import QApplication
from terminal.widget import TerminalWidget


def main():
    app = QApplication(sys.argv)

    widget = TerminalWidget(rows=24, cols=80, display_only=True)
    widget.resize(640, 480)

    # Connect signals to verify they fire
    widget.cwd_changed.connect(lambda d: print(f"[SIGNAL] cwd_changed: {d}"))
    widget.notification_received.connect(
        lambda t, m: print(f"[SIGNAL] notification: title='{t}' msg='{m}'"))
    widget.progress_changed.connect(
        lambda s, v: print(f"[SIGNAL] progress: state={s} value={v}%"))
    widget.title_changed.connect(lambda t: print(f"[SIGNAL] title: {t}"))
    widget.selection_copied.connect(
        lambda t: print(f"[SIGNAL] selection_copied: {len(t)} chars"))

    # OSC 2: Title
    widget.feed("\x1b]2;My Terminal\x1b\\")
    print("Sent: OSC 2 title")

    # OSC 7: CWD
    widget.feed("\x1b]7;file:///home/user/project\x1b\\")
    print("Sent: OSC 7 cwd")

    # OSC 8: Hyperlink
    widget.feed("\x1b]8;;https://github.com\x1b\\")
    widget.feed("GitHub Link")
    widget.feed("\x1b]8;;\x1b\\")
    widget.feed("\n")
    print("Sent: OSC 8 hyperlink 'GitHub Link'")

    # OSC 9: Simple notification
    widget.feed("\x1b]9;Build done!\x1b\\")
    print("Sent: OSC 9 notification")

    # OSC 777: Structured notification
    widget.feed("\x1b]777;notify;Status;All tests passed\x1b\\")
    print("Sent: OSC 777 notification")

    # OSC 9;4: Progress
    widget.feed("\x1b]9;4;1;50\x1b\\")
    print("Sent: OSC 9;4 progress 50%")

    print("\nCheck terminal window for hyperlink rendering (blue underline)")
    print("Signals should have fired above.")

    widget.show()
    app.exec()


if __name__ == "__main__":
    main()
