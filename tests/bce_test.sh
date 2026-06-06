#!/bin/bash
# BCE (Background Color Erase) visual test for par-term-emu-core-rust
#
# Usage:
#   bash tests/bce_test.sh | uv run python main.py --display
#
# Expected: colored rows with \x1b[K should fill the ENTIRE line width.
# Bug:      rows using \x1b[K show black after the label text instead of
#           the SGR background color, because erase ops use cell.reset()
#           which always sets bg to NamedColor::Black.

reset="\x1b[0m"

bce_test() {
    local bg=$1 label=$2
    printf "${bg}%-10s\x1b[K${reset}\n" "$label"
}

no_erase_test() {
    local bg=$1 label=$2
    printf "${bg}%-10s${reset}\n" "$label"
}

echo "=== BCE Bug: erase should fill with current SGR background ==="
echo ""

echo "With EL (\x1b[K) — should fill to right edge:"
bce_test "\x1b[42m" "GREEN+EL"
bce_test "\x1b[44m" "BLUE+EL"
bce_test "\x1b[41m" "RED+EL"
bce_test "\x1b[45m" "MAGENTA+EL"
bce_test "\x1b[43m" "YELLOW+EL"
echo ""

echo "Without EL — bg only behind text (for reference):"
no_erase_test "\x1b[42m" "GREEN"
no_erase_test "\x1b[44m" "BLUE"
no_erase_test "\x1b[41m" "RED"
echo ""

echo "If \x1b[K worked correctly:"
echo "  'GREEN+EL' row should be a full-width green bar"
echo "  'GREEN'    row should have green only behind the text"
echo ""
echo "Compare the two — if they look the same, \x1b[K is broken."
