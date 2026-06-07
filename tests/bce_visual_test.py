"""BCE (Background Color Erase) visual test with _BackgroundPropagator.

Demonstrates that pyqterminal's background propagation layer correctly handles
the BCE gap in par-term-emu-core-rust. The Rust library's erase ops always
reset bg to NamedColor::Black, but our propagator fills unwritten cells.

Usage:
    uv run python tests/bce_visual_test.py          # Text output
    uv run python tests/bce_visual_test.py --render # Pipe through --display
"""

from __future__ import annotations

_DEFAULT_FG = (192, 192, 192)
_DEFAULT_BG = (0, 0, 0)

_COLOR_NAMES: dict[tuple[int, int, int], str] = {
    (0, 128, 0):   "GREEN ",
    (0, 0, 128):   "BLUE  ",
    (128, 0, 0):   "RED   ",
    (128, 0, 128): "MAGENTA",
    (128, 128, 0): "YELLOW",
    (0, 0, 0):     "BLACK ",
}


def _bg_name(bg: tuple[int, int, int]) -> str:
    return _COLOR_NAMES.get(bg, f"({bg[0]:3d},{bg[1]:3d},{bg[2]:3d})")


def _cell_repr(char: str, bg: tuple[int, int, int]) -> str:
    """Single-cell visual representation for text-mode output."""
    if bg == (0, 128, 0):
        return f"\033[42m{char or ' '}\033[0m"
    if bg == (0, 0, 128):
        return f"\033[44m{char or ' '}\033[0m"
    if bg == (128, 0, 0):
        return f"\033[41m{char or ' '}\033[0m"
    if bg == (128, 0, 128):
        return f"\033[45m{char or ' '}\033[0m"
    if bg == (128, 128, 0):
        return f"\033[43m{char or ' '}\033[0m"
    return char or " "


def run_bce_test() -> int:
    """Run BCE test: process escape sequences, apply propagator, check results.

    Returns:
        Number of failures (0 = all good).
    """
    from par_term_emu_core_rust import Terminal
    from terminal.background_propagator import _BackgroundPropagator

    term = Terminal(40, 12)
    propagator = _BackgroundPropagator(rows=12)

    # ── Test data: each row is (description, escape_sequence, row_label) ──
    # Sequences include \r\n to advance to next line after writing.
    tests = [
        ("green bg + EL",      "\x1b[42mGREEN+EL  \x1b[K\x1b[0m\r\n",           "GREEN+EL "),
        ("blue bg + EL",       "\x1b[44mBLUE+EL   \x1b[K\x1b[0m\r\n",           "BLUE+EL  "),
        ("red bg + EL",        "\x1b[41mRED+EL    \x1b[K\x1b[0m\r\n",           "RED+EL   "),
        ("magenta bg + EL",    "\x1b[45mMAGENTA+EL\x1b[K\x1b[0m\r\n",           "MAGENTA+EL"),
        ("yellow bg + EL",     "\x1b[43mYELLOW+EL \x1b[K\x1b[0m\r\n",           "YELLOW+EL"),
        # Reference: NO EL — bg only behind text
        ("green bg, no EL",    "\x1b[42mGREEN     \x1b[0m\r\n",                  "GREEN    "),
        ("blue bg, no EL",     "\x1b[44mBLUE      \x1b[0m\r\n",                  "BLUE     "),
        ("red bg, no EL",      "\x1b[41mRED       \x1b[0m\r\n",                  "RED      "),
    ]

    failures = 0
    expected_bgs = [
        (0, 128, 0),   # green+EL
        (0, 0, 128),   # blue+EL
        (128, 0, 0),   # red+EL
        (128, 0, 128),  # magenta+EL
        (128, 128, 0),  # yellow+EL
        (0, 128, 0),   # green (no EL)
        (0, 0, 128),   # blue (no EL)
        (128, 0, 0),   # red (no EL)
    ]

    print("=" * 70)
    print("  BCE Visual Test — Background Propagation via _BackgroundPropagator")
    print("=" * 70)
    print()
    print("  Each row:  [label] | visual fill (first 30 columns)")
    print()

    for row_idx, (desc, seq, label) in enumerate(tests):
        # Feed escape sequence to terminal
        term.process_str(seq)

        # Get raw cells (Rust library — no BCE, bg=(0,0,0) after erase)
        raw_cells = term.get_line_cells(row_idx)

        # Apply background propagation (our fix)
        cells = propagator.process_cells(row_idx, raw_cells)

        # ── Verify: for "with EL" rows, trailing cells should have SGR bg ──
        expected_bg = expected_bgs[row_idx]
        has_el = "+EL" in label

        # Check a trailing cell (column 20) for EL rows
        if has_el:
            raw_bg = raw_cells[min(20, len(raw_cells) - 1)][2]
            prop_bg = cells[min(20, len(cells) - 1)][2]

            raw_ok = raw_bg != _DEFAULT_BG  # Rust lib: expected to FAIL (raw_bg=0,0,0)
            prop_ok = prop_bg == expected_bg  # Our propagator: expected to PASS

            raw_status = "\033[32mOK\033[0m" if raw_ok else "\033[31mFAIL\033[0m"
            prop_status = "\033[32mOK\033[0m" if prop_ok else "\033[31mFAIL\033[0m"

            if not prop_ok:
                failures += 1
            print(f"  [{label}] raw={raw_status}  prop={prop_status}  "
                  f"raw_bg={_bg_name(raw_bg)}  prop_bg={_bg_name(prop_bg)}")
        else:
            print(f"  [{label}] (reference — no EL, bg only behind text)")

        # ── Visual: render first 30 columns with color ──
        visual = "".join(_cell_repr(cells[c][0], cells[c][2])
                         for c in range(min(30, len(cells))))
        print(f"         {visual}")
        print()

    print("─" * 70)
    if failures == 0:
        print("  RESULT: All 5 EL rows propagated correctly ✅")
    else:
        print(f"  RESULT: {failures} failure(s) ❌")
    print("─" * 70)

    return failures


if __name__ == "__main__":
    raise SystemExit(run_bce_test())
