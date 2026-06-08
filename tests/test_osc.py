"""Test OSC sequences in pyqterminal display-only mode.

Usage:
    uv run python tests/test_osc.py | uv run python main.py --display
"""

import base64
import sys
import time


def osc(code, payload=""):
    """Write an OSC escape sequence."""
    sys.stdout.write(f"\x1b]{code};{payload}\x1b\\")
    sys.stdout.flush()

def wait(ms=500):
    time.sleep(ms / 1000)

# ── OSC 0/2: Window Title ──
print("=== OSC 0/2: Window Title ===")
osc(0, "My Terminal Title")
wait()
osc(2, "Updated Title")
wait()

# ── OSC 7: Current Directory ──
print("=== OSC 7: Current Directory ===")
osc(7, "file:///home/user/projects/pyqterminal")
print("(check cwd_changed signal)")
wait()

# ── OSC 8: Hyperlinks ──
print("=== OSC 8: Hyperlinks ===")
osc(8, ";;https://github.com")
print("Clickable: GitHub (Ctrl+Click to open)")
osc(8, ";;")
print()
wait()

osc(8, ";;https://pypi.org")
print("Clickable: PyPI (Ctrl+Click to open)")
osc(8, ";;")
print()
wait()

# ── OSC 9: Simple Notification ──
print("=== OSC 9: Simple Notification ===")
osc(9, "Build completed successfully!")
wait()

# ── OSC 777: Structured Notification ──
print("=== OSC 777: Structured Notification ===")
osc("777;notify;Build Status;Compilation failed with 3 errors")
wait()

# ── OSC 9;4: Progress Bar ──
print("=== OSC 9;4: Progress Bar ===")
for pct in [0, 25, 50, 75, 100]:
    osc("9;4;1", str(pct))
    print(f"Progress: {pct}%")
    wait(300)
osc("9;4;0")  # hide
print("Progress: hidden")
wait()

# ── OSC 52: Clipboard ──
print("=== OSC 52: Clipboard ===")
text = "Hello from pyqterminal OSC 52 test!"
encoded = base64.b64encode(text.encode()).decode()
osc("52;c", encoded)
print(f"Clipboard set to: {text}")
wait()

print("\n=== All OSC tests complete ===")
