# AGENTS.md

## Setup & Commands

- **Python:** 3.12.13 exactly (`.python-version`). Required by `par-term-emu-core-rust` prebuilt wheels.
- **Package manager:** `uv` (not pip). `uv sync` to install deps. `uv add <pkg>` to add.
- **Run:** `uv run python main.py`
- **Lint/format/test:** None configured yet. `tests/` directory exists but is empty.

## Architecture

A cross-platform terminal emulator with a Rust backend and PySide6 frontend.

```
main.py → TerminalWidget (QWidget) → PtyTerminal (Rust via par-term-emu-core-rust)
            ├── InputHandler (QKeyEvent → bytes)
            └── QPainter rendering directly in paintEvent()
```

- **Backend:** `par_term_emu_core_rust.PtyTerminal` — Rust `vte` crate under the hood. Handles PTY, escape sequence parsing, buffer, colors, cursor, scrollback, damage tracking.
- **Frontend:** Two Python files under `terminal/`:
  - `widget.py` (~492 lines) — TerminalWidget (QPainter rendering, keyboard/mouse/selection/scrollback/zoom/window resize)
  - `input_handler.py` (~103 lines) — QKeyEvent → terminal bytes
- **Entry point:** `main.py` — creates QApplication, TerminalWidget, calls `start_shell()`, runs event loop.
- **No QPixmap double buffer** — removed due to Retina/HiDPI devicePixelRatio issues (Error #5 in ERRORS.md). Render directly on the widget's QPainter in `paintEvent()`.

## Critical API Gotchas (read ERRORS.md first)

These are real API names discovered via `dir()`, not from documentation — the design doc (`DESIGN.md`) contains speculative API names that differ from reality.

| Expectation (wrong) | Reality |
|---|---|
| `get_cell_char(row, col)` | `get_line_cells(row)` returns `list[(char, fg, bg, attrs), ...]` for all cols |
| `damage_regions_since(gen)` | Use `has_updates_since(gen)` + read cells directly; the code no longer uses incremental damage regions |
| `process_str()` on PtyTerminal | Only exists on headless `Terminal` class. PtyTerminal reads PTY internally via `spawn_shell()`. |
| Integer cursor style | `cursor_style()` returns `CursorStyle` enum (e.g. `CursorStyle.BlinkingBlock`) |
| `write_str()` takes bytes | `write_str()` takes `str`. Use `write()` for `bytes`. |

## Rendering Rules (from hard-won fixes)

1. **Background fill BEFORE space check.** Space characters with colored backgrounds must have the background drawn. The `_render_cells` loop does `fillRect` before skipping spaces. Do not reorder.
2. **No QPixmap.** Render directly in `paintEvent()` via `QPainter(self)`. Qt handles devicePixelRatio automatically.
3. **Font selection** tries multiple monospace fonts in priority order (SF Mono → JetBrains Mono → Fira Code → Menlo → Courier New → monospace). Fallback to "monospace" if none found.
4. **Reverse video (SGR 7).** `attrs.reverse` must be handled — when `True`, swap fg and bg colors with proper default fallbacks. The library does NOT pre-swap; the renderer is responsible. Missing this causes nano/tmux bars and other reverse-video content to render with invisible background.
5. **Hidden text (SGR 8).** `attrs.hidden` — show background only, skip text. Used for password prompts. Place check after background fill, before text draw.
6. **Wide chars (CJK).** `attrs.wide_char` and `attrs.wide_char_spacer` — skip spacer cells entirely. Wide chars occupy 2 columns; the library advances the column index automatically.
7. **Blink (SGR 5).** `attrs.blink` — uses `_blink_visible` flag toggled by cursor timer (~530ms). Hide text during blink-off phase.
8. **Dim (SGR 2).** `attrs.dim` — reduce fg RGB by half (`c // 2`).
9. **Strikethrough (SGR 9).** `attrs.strikethrough` — horizontal line at cell midpoint.
10. **Underline styles (SGR 4:N).** `attrs.underline_style` (UnderlineStyle enum): Straight, Double (two lines), Curly (dashed approx), Dotted (Qt.DotLine), Dashed (Qt.DashLine).

## Scrollback

- `_scroll_offset` tracks how far back the user has scrolled (0 = live view).
- `scrollback_line(idx)` returns cell data for scrollback rows.
- `scrollback_len()` returns total scrollback buffer size.
- When scrolled back and new output arrives, a yellow indicator bar appears at the bottom-right.
- Shift+PageUp/PageDown scrolls. Mouse wheel scrolls too (with granularity smoothing via `_wheel_accum`).

## Selection & Clipboard

- Mouse drag selects text (row, col based selection).
- Selection is automatically copied on mouse release.
- Cmd+C (macOS) / Ctrl+Shift+C copies existing selection.
- Cmd+V (macOS) / Ctrl+Shift+V pastes clipboard.
- Middle-click pastes clipboard.
- Right-click context menu: Copy, Paste, Zoom In/Out/Reset.

## Zoom

- Ctrl++ / Ctrl+- / Ctrl+0 (macOS) or Ctrl+Shift++ / Ctrl+Shift+- (other platforms) change font size.
- Min size 6pt, max 32pt.
- Resize triggers terminal resize to match new cell dimensions.

## Design Docs

- `DESIGN.md` — Architecture design doc (Chinese). The architecture sections (§4-§6) reflect the intended design, but the actual implementation has simplified (no damage_regions, no QPixmap buffer). The API names in the design doc code examples are speculative — trust the actual code over them.
- `ERRORS.md` — Error log with 6 documented mistakes and their root causes. **Read this before touching `widget.py`.** Contains PySide6 and par-term-emu-core-rust trap checklists.
