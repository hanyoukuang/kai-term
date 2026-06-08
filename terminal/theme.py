"""Theme and font configuration for pyqterminal.

Provides default color constants, font candidate list, and monospace font
auto-detection logic used by TerminalWidget.
"""

from PySide6.QtGui import QColor, QFont, QFontMetrics

# ── Default colors ──────────────────────────────────────────────────────

DEFAULT_FG = QColor(192, 192, 192)  # Light grey
DEFAULT_BG = QColor(0, 0, 0)        # Black

# ── Font candidates ─────────────────────────────────────────────────────

_FONT_CANDIDATES = (
    "MesloLGS NF", "JetBrainsMono Nerd Font",
    "FiraCode Nerd Font", "CaskaydiaCove Nerd Font",
    "Hack Nerd Font", "DejaVuSansMono Nerd Font",
    "SF Mono", "JetBrains Mono", "Fira Code",
    "Menlo", "Courier New", "monospace",
)


def pick_monospace_font(size: int = 13) -> QFont:
    """Auto-detect the first available monospace font from candidate list.

    Tries Nerd Fonts first (for icon glyph support), then system monospace fonts.
    Falls back to "monospace" if none found.
    """
    for family in _FONT_CANDIDATES:
        font = QFont(family, size)
        font.setStyleHint(QFont.Monospace)
        font.setHintingPreference(QFont.PreferVerticalHinting)
        fm = QFontMetrics(font)
        if fm.horizontalAdvance("M") > 0:
            return font
    return QFont("monospace", size)
