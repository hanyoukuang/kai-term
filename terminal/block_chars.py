"""Unicode block element rendering (U+2580–U+259F).

Draws block characters as filled rectangles instead of font glyphs,
eliminating sub-pixel gaps between adjacent cells (e.g. progress bars,
split-pane separators).
"""

from PySide6.QtGui import QColor, QPainter


def draw_block_fill(painter: QPainter, char: str, x: int, y: int,
                     cell_w: int, cell_h: int, fg_rgb: tuple) -> bool:
    """Draw Unicode block element as filled rectangle.

    Returns True if drawn, False to fallback to font rendering.
    Draws as filled rect to eliminate sub-pixel gaps between adjacent cells.
    """
    cp = ord(char)
    color = QColor(*fg_rgb)

    if cp == 0x2588:                          # █ FULL BLOCK
        painter.fillRect(x, y, cell_w, cell_h, color)
    elif cp == 0x2580:                        # ▀ UPPER HALF BLOCK
        painter.fillRect(x, y, cell_w, cell_h // 2, color)
    elif cp == 0x2584:                        # ▄ LOWER HALF BLOCK
        half = cell_h // 2
        painter.fillRect(x, y + half, cell_w, cell_h - half, color)
    elif cp == 0x258C:                        # ▌ LEFT HALF BLOCK
        painter.fillRect(x, y, cell_w // 2, cell_h, color)
    elif cp == 0x2590:                        # ▐ RIGHT HALF BLOCK
        half = cell_w // 2
        painter.fillRect(x + half, y, cell_w - half, cell_h, color)
    elif 0x2581 <= cp <= 0x2587:              # ▁-▇ Lower 1/8 … 7/8
        frac = (cp - 0x2580) / 8
        fill_h = max(1, int(cell_h * frac))
        painter.fillRect(x, y + cell_h - fill_h, cell_w, fill_h, color)
    elif 0x2589 <= cp <= 0x258F:              # ▉-▏ Left 7/8 … 1/8
        frac = (0x2590 - cp) / 8
        fill_w = max(1, int(cell_w * frac))
        painter.fillRect(x, y, fill_w, cell_h, color)
    elif cp == 0x2594:                        # ▔ UPPER 1/8 BLOCK
        painter.fillRect(x, y, cell_w, max(1, cell_h // 8), color)
    elif cp == 0x2595:                        # ▕ RIGHT 1/8 BLOCK
        fill_w = max(1, cell_w // 8)
        painter.fillRect(x + cell_w - fill_w, y, fill_w, cell_h, color)
    else:
        return False  # shade / quadrant — use font
    return True
