"""Theme and font configuration for pyqterminal.

Provides default color constants, font candidate list, and monospace font
auto-detection logic used by TerminalWidget.
"""

import os
from PySide6.QtGui import QColor, QFont, QFontDatabase, QFontMetrics

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

_BUNDLED_FONT_FAMILY: str | None = None


def _load_bundled_font() -> str | None:
    """Load the bundled font if available and return its family name."""
    global _BUNDLED_FONT_FAMILY
    if _BUNDLED_FONT_FAMILY is not None:
        return _BUNDLED_FONT_FAMILY if _BUNDLED_FONT_FAMILY != "" else None

    current_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(current_dir, "assets", "fonts", "JetBrainsMonoNerdFont-Regular.ttf")
    if os.path.exists(font_path):
        # On Windows, Qt expects forward slashes for font paths.
        font_id = QFontDatabase.addApplicationFont(font_path.replace("\\", "/"))
        if font_id != -1:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                _BUNDLED_FONT_FAMILY = families[0]
                return _BUNDLED_FONT_FAMILY

    _BUNDLED_FONT_FAMILY = ""
    return None


def pick_monospace_font(size: int = 13) -> QFont:
    """Auto-detect the first available monospace font from candidate list.

    Tries the bundled Nerd Font first, then system monospace fonts.
    Falls back to "monospace" if none found.
    """
    bundled_family = _load_bundled_font()
    if bundled_family:
        font = QFont(bundled_family, size)
        font.setStyleHint(QFont.Monospace)
        font.setHintingPreference(QFont.PreferVerticalHinting)
        return font

    for family in _FONT_CANDIDATES:
        font = QFont(family, size)
        font.setStyleHint(QFont.Monospace)
        font.setHintingPreference(QFont.PreferVerticalHinting)
        fm = QFontMetrics(font)
        if fm.horizontalAdvance("M") > 0:
            return font
    return QFont("monospace", size)
