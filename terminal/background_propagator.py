"""背景色传播预处理。

BCE (Background Color Erase) 已由 par-term-emu-core-rust v0.42.3 实现。
本模块仅处理 BCE 未覆盖的场景：从未写入过的单元格（bg=(0,0,0) + 空字符）
通过行内一致性检查 + 紧邻行 1 跳继承传播有效背景色。
"""

from __future__ import annotations


class _BackgroundPropagator:
    """背景色传播预处理器。"""

    def __init__(self, rows: int) -> None:
        self._rows = rows
        self._row_bg_cache: list[tuple[int, int, int] | None] = [None] * rows

    # ── cell 判断 ──────────────────────────────────────────────────────

    @staticmethod
    def _is_unwritten(cell: tuple) -> bool:
        char, _fg, bg, attrs = cell
        if bg != (0, 0, 0):
            return False
        if char and char not in ("", " ", "\x00"):
            return False
        return not (attrs and attrs.reverse)

    # ── 行背景推断 ─────────────────────────────────────────────────────

    @staticmethod
    def _row_bg(cells: list) -> tuple[int, int, int] | None:
        """行内所有非默认背景单元格颜色一致时返回该色，否则返回 None。"""
        first: tuple[int, int, int] | None = None
        for _ch, _fg, bg, attrs in cells:
            if attrs and (attrs.wide_char_spacer or attrs.reverse):
                continue
            if bg == (0, 0, 0):
                continue
            if first is None:
                first = bg
            elif bg != first:
                return None
        return first

    # ── 主入口 ─────────────────────────────────────────────────────────

    def process_cells(self, row_idx: int, cells: list, live: bool = True) -> list:
        """处理一行 cells，填充未写入单元格的背景色。

        live=True 时从上一行自身背景继承（1 跳），继承来的背景不缓存。
        live=False 时仅行内传播。
        """
        own_bg = self._row_bg(cells)

        eff_bg: tuple[int, int, int] | None = None
        if own_bg is not None:
            eff_bg = own_bg
            if live and 0 <= row_idx < self._rows:
                self._row_bg_cache[row_idx] = eff_bg
        elif live and row_idx > 0:
            eff_bg = self._row_bg_cache[row_idx - 1]

        if eff_bg is None:
            return cells

        result: list = []
        for cell in cells:
            if self._is_unwritten(cell):
                result.append((cell[0], cell[1], eff_bg, cell[3]))
            else:
                result.append(cell)
        return result

    # ── 缓存管理 ───────────────────────────────────────────────────────

    def reset(self) -> None:
        self._row_bg_cache = [None] * self._rows
