# pyqterminal — 跨平台终端模拟器 架构设计文档

> **状态**：方案已确认，进入实现阶段  
> **创建日期**：2026-06-02  
> **更新日期**：2026-06-02（v2：切换为 Rust 解析器方案）  
> **关联文件**：`ERRORS.md`（错误记录，详见检查点 #0）  
> **关键决策**：Python 3.12+ / Rust 解析器 / Windows 延期

---

## 目录

1. [需求分析](#1-需求分析)
2. [技术调研结论](#2-技术调研结论)
3. [方案对比与选择](#3-方案对比与选择)
4. [推荐架构设计](#4-推荐架构设计)
5. [核心模块设计](#5-核心模块设计)
6. [数据流设计](#6-数据流设计)
7. [实现路线图](#7-实现路线图)
8. [检查点清单](#8-检查点清单)
9. [风险与待确认事项](#9-风险与待确认事项)

---

## 1. 需求分析

### 1.1 核心需求

| 需求 | 描述 | 优先级 |
|------|------|--------|
| 跨平台 | macOS / Linux / Windows | P0 |
| xterm-256color | 解析 256 色调色板 + True Color (24-bit) | P0 |
| 复杂 TUI | 支持 nano、vim、htop、tmux 等 | P0 |
| 自适应窗口 | 窗口大小变化时自动调整行列数和文字渲染 | P0 |
| 原生 PySide6 | 不依赖 QWebEngine、非 Qt 原生渲染 | P0 |
| 性能 | vim 打字流畅不卡顿（≥30fps） | P1 |
| 滚动回看 | 保留历史输出（scrollback buffer） | P2 |

### 1.2 vim/nano 的特殊需求

vim 和 nano 是 **alternate-screen** 应用，它们的行为与普通终端程序不同：

- 启动时切换到 **备用屏幕缓冲区**（DECSET 1049: `\x1b[?1049h`）
- 使用**光标定位**而非滚动来更新画面
- 大量使用 256 色/True Color 实现语法高亮
- 频繁的短小 escape 序列（每次光标移动都会产生）
- vim 分屏需要 **scroll region** 支持（DECSTBM: `\x1b[r`）
- vim 的 insert/normal 模式切换需要 **光标形状变化**（DECSCUSR: `\x1b[ q`）
- 输入处理需区分键盘事件和终端控制序列

---

## 2. 技术调研结论

### 2.1 来自 xterm.js 的关键启示

xterm.js（27000+ stars，VS Code 内置终端）是生产级 JavaScript 终端模拟器，其架构模式可作为参考：

| 概念 | xterm.js 实现 | Python 映射 |
|------|--------------|-------------|
| **Parser** | FSM 状态机（8状态/79转移），Uint16Array 转移表 | pyte.Stream 或自建 Python FSM |
| **Buffer** | CircularList<BufferLine>，3坐标系统 (y/ybase/ydisp) | pyte.DiffScreen 或自建环形缓冲 |
| **Cell** | 3×Uint32 打包 (codepoint, fg, bg) | pyte.Char 或自建 namedtuple/dataclass |
| **Renderer** | WebGL/DOM，脏行跟踪增量渲染 | QPainter + QPixmap，脏行跟踪 |
| **Flow Control** | WriteBuffer，12ms 时间切片，50MB 上限 | QSocketNotifier，分块处理 |
| **Alt Buffer** | BufferSet 管理 normal/alt 切换 | pyte.Screen 内置支持 |

**核心架构启示**：
1. **Parser 与 State 分离** — FSM 只做序列识别，不修改状态
2. **使用环形数组**做 scrollback，避免无限增长
3. **打包 Cell 数据**紧凑存储（3 个 int 表示一个单元格）
4. **脏行跟踪**实现增量渲染，不全屏重绘
5. **坐标系统**：`ybase + y = 环形缓冲中的绝对行号`

### 2.2 终端解析引擎调研（重新调研 — Rust 方向）

基于用户决策（Python ≥3.12 + Rust 解析器），对 Rust 终端模拟库进行了全面调研：

| Crate | Python绑定 | VT支持 | TrueColor | Sixel | Kitty | PTY | 预编译 |
|-------|-----------|--------|-----------|-------|-------|-----|--------|
| **par-term-emu-core-rust** | ✅ PyPI wheel | VT520 | ✅ | ✅ | ✅ (v0.42+) | ✅ 内置 | ✅ |
| alacritty_terminal | ❌ 需自建 | ~VT500 | ✅ | ✅ | ❌ | 需外部 | ❌ |
| wezterm-term | ❌ 需自建 | ~VT500 | ✅ | ✅ | ✅ | ❌ | ❌ |
| vt100-rust | ❌ 需自建 | VT100 基本 | ✅ | ❌ | ❌ | ❌ | ❌ |

**结论：`par-term-emu-core-rust` 是唯一有预编译 Python 绑定的 Rust 终端模拟器。**

#### 关键信息

| 属性 | 值 |
|------|-----|
| **PyPI** | `pip install par-term-emu-core-rust` |
| **版本** | v0.42.2 (2026-05-29)，59 个版本 |
| **许可证** | MIT |
| **Python** | ≥3.12 |
| **平台** | Linux(x86_64/ARM64), macOS(Intel/Apple Silicon), Windows(x86_64) |
| **内部解析器** | alacritty 的 `vte` crate（56M+ 下载量，行业标准） |
| **PTY** | `portable-pty` crate，跨平台内置 |
| **GitHub** | paulrobello/par-term-emu-core-rust，12 stars，410 commits |
| **状态** | Beta (PyPI status 4)，但功能完整 |

#### 核心 Python API

```python
from par_term_emu_core_rust import PtyTerminal

# 创建终端 + 启动 shell
with PtyTerminal(80, 24) as term:
    term.spawn_shell()
    
    # 发送输入
    term.write_str("echo hello\n")
    
    # 检查更新（增量渲染的关键）
    gen = 0
    while term.has_updates_since(gen):
        for region in term.damage_regions_since(gen):
            # region = (start_row, end_row) — 只重绘这些行
            for row in range(region[0], region[1] + 1):
                for col in range(80):
                    char = term.get_cell_char(row, col)
                    fg = term.get_fg_color(row, col)
                    bg = term.get_bg_color(row, col)
        gen = term.update_generation()
    
    # 调整终端尺寸（自适应窗口）
    term.resize(rows, cols)
    
    # 查询光标
    cx, cy = term.cursor_position()
    visible = term.cursor_visible()
```

**关键 API 清单**：
- `term.process(data)` / `term.process_str(data)` — 喂入数据（解析 escape 序列）
- `term.write_str(data)` — 发送数据到 PTY
- `term.has_updates_since(gen)` — 是否有新内容需要渲染
- `term.damage_regions_since(gen)` — 获取脏区域列表 → **替代 pyte 的 DiffScreen.dirty**
- `term.update_generation()` — 前移代数计数器
- `term.get_cell_char(row, col)` / `get_fg_color()` / `get_bg_color()` — 逐格查询
- `term.resize(rows, cols)` — 调整终端尺寸
- `term.cursor_position()` / `cursor_visible()` — 光标状态
- `term.drain_responses()` — 获取终端响应
- `term.poll_events()` — 事件轮询（鼠标、模式变化等）
- `term.cell_pixel_width()` / `term.cell_pixel_height()` — 参考单元格像素尺寸

### 2.3 渲染方案对比（关键决策）

| 方案 | 可行性 | 性能 | 开发量 | 说明 |
|------|--------|------|--------|------|
| **QTextEdit / QPlainTextEdit** | ❌ 不可行 | 极差 | 少 | 无固定网格、无法定位光标、ANSI 解析困难 |
| **QPainter 自定义 Widget** | ✅ 推荐 | 高 | 中 | QTermWidget 的 3716 行 C++ 即用此方案 |
| **QOpenGLWidget** | ⚠️ 过度 | 极高 | 高 | 对终端来说过度优化，增加复杂性 |
| **QGraphicsView** | ⚠️ 可用 | 中 | 中 | 适合但不如 QPainter 直接 |

**结论：QPainter + QPixmap 双缓冲是标准方案**，被 QTermWidget、Konsole、iTerm2 等项目采用。

### 2.4 PTY 方案

`par-term-emu-core-rust` 已内置 `portable-pty`（跨平台 PTY），通过 `PtyTerminal` 直接使用。无需额外集成 Python 的 `pty` 模块。

| 平台 | 方案 | 说明 |
|------|------|------|
| Linux/macOS | `PtyTerminal.spawn_shell()` | 内置，无需手动处理 |
| Windows | `PtyTerminal.spawn_shell()` | 内置，基于 ConPTY |
| 高级控制 | `term.spawn_shell(env=..., cwd=...)` | 传递环境变量和工作目录 |

---

## 3. 最终方案：par-term-emu-core-rust + 自建 PySide6 Widget ✅

### 选择理由

| 维度 | 说明 |
|------|------|
| **解析引擎** | Rust 原生 `vte` crate（alacritty 同款），56M+ 下载量，性能无忧 |
| **集成难度** | `pip install` 预编译 wheel，零编译，`import` 即用 |
| **功能完整度** | VT520 + TrueColor + Sixel + Kitty Graphics + 鼠标跟踪 + Shell Integration |
| **增量渲染** | 内置 `damage_regions_since()` API，无需像 pyte 那样包装 DiffScreen |
| **PTY 管理** | 内置 `portable-pty`，无需手动 `pty.fork()` + `fcntl.ioctl()` |
| **渲染层** | 仅需实现 QPainter Widget（~1000-1500 行），从 `PtyTerminal` 查询单元格颜色 |
| **Python 版本** | ≥3.12，通过 uv 管理（已安装 3.12.13） |

### 架构简化对比

| 原方案 (pyte) | 新方案 (Rust) |
|--------------|---------------|
| pyte.Stream（FSM 解析器） | PtyTerminal.process()（Rust 内部处理） |
| pyte.DiffScreen（缓冲 + 脏行） | PtyTerminal 内置（damage_regions_since） |
| TerminalScreenManager（包装层） | ❌ 不再需要 |
| PTYManager（pty.fork + QSocketNotifier） | PtyTerminal 内置（spawn_shell + write_str） |
| InputHandler（键盘编码） | 仍需要（QKeyEvent → bytes） |
| TerminalWidget（QPainter 渲染） | 仍需要，但更简单（直接查询终端 API） |

---

## 4. 推荐架构设计

### 4.1 分层架构（精简版）

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  main.py: QApplication, 窗口管理, 主题配置                  │
├─────────────────────────────────────────────────────────────┤
│                     UI Layer (PySide6)                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           TerminalWidget (QWidget)                   │   │
│  │  - paintEvent(): QPainter 渲染（查询 PtyTerminal）   │   │
│  │  - keyPressEvent(): 键盘 → InputHandler → write_str │   │
│  │  - resizeEvent(): resize → 重算行列数              │   │
│  │  - mouse events: 文本选择                           │   │
│  │  - QPixmap 双缓冲                                    │   │
│  │  - QTimer 光标闪烁 + 轮询 has_updates_since()       │   │
│  └────────────────────┬─────────────────────────────────┘   │
│                       │ 读写                                │
│  ┌────────────────────▼─────────────────────────────────┐   │
│  │        par_term_emu_core_rust.PtyTerminal            │   │
│  │  - 解析 escape 序列（内部 vte crate）                │   │
│  │  - 维护终端状态（缓冲、光标、滚动、颜色）            │   │
│  │  - PTY 管理（内部 portable-pty）                      │   │
│  │  - damage_regions_since() → 脏区域跟踪               │   │
│  │  - get_cell_char/fg_color/bg_color() → 单元格查询    │   │
│  │  - spawn_shell() / write_str() / resize()            │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 关键组件关系图（精简版）

```
      ┌──────────────────────────────────────────────────┐
      │              PtyTerminal (Rust)                  │
      │                                                  │
      │  ┌──────────┐   ┌──────────┐   ┌────────────┐  │
      │  │ vte 解析  │   │  终端缓冲 │   │ portable-  │  │
      │  │  (FSM)   │──▶│  (Grid)  │   │   pty      │  │
      │  └──────────┘   └────┬─────┘   └──────┬─────┘  │
      │                      │                 │        │
      │     damage_regions   │          PTY I/O│        │
      │     get_cell_*()     │                 │        │
      └──────────────────────┼─────────────────┼────────┘
                             │                 │
              ┌──────────────▼──┐     ┌───────▼────────┐
              │  TerminalWidget │     │    Shell 进程    │
              │  (QPainter)     │◄────│  (bash/zsh)     │
              │  - paintEvent   │     └───────┬────────┘
              │  - keyPressEvent│─────────────┘
              └─────────────────┘    write_str()
```

**架构关键变化**：
- ❌ 不再需要 `TerminalScreenManager`（pyte DiffScreen 包装器）
- ❌ 不再需要 `PTYManager`（pty.fork + QSocketNotifier）
- ❌ 不再需要 `CellStyle` 转换层（Rust 直接返回 RGB 元组）
- ✅ 仅需 `TerminalWidget`（渲染）+ `InputHandler`（键盘编码）

---

## 5. 核心模块设计（精简版）

Rust 解析器承担了大部分工作，Python 端只需两个核心模块：

### 5.1 `terminal/widget.py` — 终端 Widget

```python
from par_term_emu_core_rust import PtyTerminal
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPainter, QPixmap, QFont, QFontMetrics, QColor, QKeyEvent

class TerminalWidget(QWidget):
    """PySide6 终端显示 Widget"""
    
    def __init__(self, parent=None, rows=24, cols=80):
        super().__init__(parent)
        
        # Rust 终端引擎
        self._term = PtyTerminal(cols, rows)
        self._generation: int = 0
        
        # 字体与尺寸
        self._font = QFont("Menlo", 13)  # 等宽字体
        self._font.setStyleHint(QFont.Monospace)
        self._fm = QFontMetrics(self._font)
        self._cell_w = self._fm.horizontalAdvance("M")
        self._cell_h = self._fm.height()
        self._rows = rows
        self._cols = cols
        
        # 渲染状态
        self._pixmap: QPixmap = None
        self._cursor_visible = True
        
        self._setup_ui()
        self._start_shell()
        
    def _setup_ui(self):
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        self.setMinimumSize(self._cell_w * 20, self._cell_h * 5)
        
        # 光标闪烁
        self._cursor_timer = QTimer(self)
        self._cursor_timer.timeout.connect(self._toggle_cursor)
        self._cursor_timer.start(530)
        
        # 终端更新轮询 (~60fps)
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._poll_updates)
        self._update_timer.start(16)
        
    def _start_shell(self):
        self._term.spawn_shell()
        self._rebuild_pixmap()
        
    def _poll_updates(self):
        """轮询终端更新 → 增量渲染脏区域"""
        if self._term.has_updates_since(self._generation):
            dirty = self._term.damage_regions_since(self._generation)
            self._repaint_regions(dirty)
            self._generation = self._term.update_generation()
        
    def _repaint_regions(self, regions: list):
        """只重绘脏区域的行（关键性能优化）"""
        painter = QPainter(self._pixmap)
        painter.setFont(self._font)
        
        for start_row, end_row in regions:
            for row in range(start_row, end_row + 1):
                if row >= self._rows:
                    break
                self._draw_row(painter, row)
                
        painter.end()
        self.update()
        
    def _draw_row(self, painter: QPainter, row: int):
        """绘制一行（背景 + 前景字符）"""
        y = row * self._cell_h
        for col in range(self._cols):
            x = col * self._cell_w
            
            # 背景色
            bg = self._term.get_bg_color(row, col)
            if bg and bg != (0, 0, 0):  # 默认黑背景跳过
                painter.fillRect(x, y, self._cell_w, self._cell_h, 
                                QColor(*bg))
            
            # 前景字符
            char = self._term.get_cell_char(row, col)
            if char and char != " ":
                fg = self._term.get_fg_color(row, col)
                if fg:
                    painter.setPen(QColor(*fg))
                painter.drawText(x, y + self._fm.ascent(), char)
                
    def resizeEvent(self, event):
        """窗口大小变化 → 重算行列数 → 通知 PTY"""
        self._cols = max(1, self.width() // self._cell_w)
        self._rows = max(1, self.height() // self._cell_h)
        self._term.resize(self._rows, self._cols)
        self._rebuild_pixmap()
        self._repaint_all()
        
    def keyPressEvent(self, event: QKeyEvent):
        """键盘输入 → 编码 → 发送到 PTY"""
        data = InputHandler.encode(event)
        if data:
            self._term.write_str(data.decode() if isinstance(data, bytes) else data)
            
    def _rebuild_pixmap(self):
        self._pixmap = QPixmap(self._cols * self._cell_w, 
                                self._rows * self._cell_h)
        self._pixmap.fill(QColor(0, 0, 0))  # 默认黑背景
        
    def _repaint_all(self):
        painter = QPainter(self._pixmap)
        painter.setFont(self._font)
        for row in range(self._rows):
            self._draw_row(painter, row)
        painter.end()
        self.update()
        
    def paintEvent(self, event):
        if self._pixmap:
            painter = QPainter(self)
            painter.drawPixmap(0, 0, self._pixmap)
            
    def _toggle_cursor(self):
        self._cursor_visible = not self._cursor_visible
        # 只重绘光标行
        cx, cy = self._term.cursor_position()
        self._repaint_regions([(cy, cy)])
```

### 5.2 `terminal/input_handler.py` — 键盘输入编码

```python
class InputHandler:
    """将 QKeyEvent 编码为终端输入序列"""
    
    @staticmethod
    def encode(event: QKeyEvent) -> bytes:
        """编码键盘事件 → 终端字节序列"""
        # 详见阶段 5 实现
        # 普通字符: event.text().encode()
        # Ctrl+C: b'\x03'
        # 方向键上: b'\x1b[A' (application模式) 或 b'\x1bOA' (normal模式)
        # F1: b'\x1bOP'
        pass
```

### 5.3 项目结构（精简版）

```
terminal/
├── pyproject.toml             # uv 项目配置
├── main.py                    # QApplication + TerminalWidget
├── DESIGN.md                  # 本文件
├── ERRORS.md                  # 错误记录
├── terminal/
│   ├── __init__.py
│   ├── widget.py              # TerminalWidget（QPainter 渲染）
│   └── input_handler.py       # 键盘输入编码
└── tests/
    ├── test_widget.py
    └── test_input_handler.py
```

> **对比原方案**：去掉了 `cell.py`, `colors.py`, `screen_manager.py`, `pty_manager.py`。Rust 引擎已处理颜色调色板和 PTY 管理。

---

## 6. 数据流设计（精简版）

### 6.1 数据流方向

```
                键盘输入
                   │
    QKeyEvent ─────┼──► InputHandler.encode() ──► bytes
                   │                                │
                   │                    term.write_str(data)
                   │                                │
                   │                          Shell 进程
                   │                                │
                   │                          PTY 输出
                   │                                │
                   │              Rust vte 解析器（内部）
                   │                                │
    ┌──────────────▼────────────────────────────────▼──┐
    │              PtyTerminal (Rust)                    │
    │  - process(data) 解析 escape 序列                 │
    │  - 维护 Grid 缓冲 + 光标 + 滚动                    │
    │  - 追踪 damage_regions                            │
    └──────────────────────┬────────────────────────────┘
                           │
    QTimer (16ms) ─────────┼──► has_updates_since(gen)?
                           │        ↓ YES
                           │    damage_regions_since(gen)
                           │        ↓
    ┌──────────────────────▼────────────────────────────┐
    │  TerminalWidget._repaint_regions(regions)         │
    │  - for each dirty region:                         │
    │    for (row, col):                                │
    │      char = term.get_cell_char(row, col)          │
    │      fg   = term.get_fg_color(row, col)           │
    │      bg   = term.get_bg_color(row, col)           │
    │      → QPainter.drawText() / fillRect()           │
    │  - QPixmap bitBlt → 屏幕                          │
    └───────────────────────────────────────────────────┘
```

### 6.2 性能关键路径

```
PTY 输出 → Rust vte 解析（纳秒级）
         → PtyTerminal 缓冲更新
         → damage_regions_since(gen) → [(row_start, row_end), ...]
         → QTimer 轮询 (16ms ≈ 60fps)
         → QPainter 增量渲染脏行到 QPixmap
         → update() 触发 paintEvent → bitBlt 到屏幕
```

---

## 7. 实现路线图（精简版）

### 阶段 0：项目初始化 ✅ 检查点 #0

- [ ] `uv init` 初始化 Python 3.12 项目
- [ ] `uv add pyside6 par-term-emu-core-rust`
- [ ] 创建项目结构：`terminal/widget.py`, `terminal/input_handler.py`, `main.py`
- [ ] 创建 `ERRORS.md`
- [ ] 测试：`uv run python -c "from par_term_emu_core_rust import Terminal; print('OK')"`

### 阶段 1：基础渲染 ✅ 检查点 #1

- [ ] `terminal/widget.py` — TerminalWidget 基础框架
- [ ] 等宽字体选择，测量 cell_w / cell_h
- [ ] QPainter + QPixmap 双缓冲
- [ ] 手动填充 PtyTerminal 数据 → 渲染网格
- [ ] resizeEvent 自适应行列数
- [ ] 测试：用 PtyTerminal.process_str("Hello World\n") 写内容并渲染

### 阶段 2：PTY 集成 ✅ 检查点 #2

- [ ] `PtyTerminal.spawn_shell()` 启动 shell
- [ ] QTimer 轮询 `has_updates_since()` + `damage_regions_since()`
- [ ] 增量渲染脏区域
- [ ] `term.resize(rows, cols)` 自适应
- [ ] 测试：启动 bash，看到提示符，输入命令看到输出

### 阶段 3：escape 序列渲染 ✅ 检查点 #3

- [ ] 前景色/背景色渲染（`get_fg_color` / `get_bg_color`）
- [ ] 光标渲染 + 闪烁
- [ ] SGR 属性支持（Rust 引擎已解析，渲染层只需应用颜色）
- [ ] 测试：`ls --color`, `echo -e "\x1b[31mRED\x1b[0m"`, `htop` 颜色正常

### 阶段 4：键盘输入 ✅ 检查点 #4

- [ ] `terminal/input_handler.py` — QKeyEvent → bytes
- [ ] 普通字符、Enter、Tab、Backspace、方向键
- [ ] Ctrl 组合键 (Ctrl+C, Ctrl+D, Ctrl+Z)
- [ ] 功能键 F1-F12
- [ ] 测试：在 bash 中编辑命令，运行 `nano` 基本操作

### 阶段 5：复杂 TUI ✅ 检查点 #5

- [ ] 验证 vim 正常显示和操作（Rust 引擎已支持所有 escape 序列）
- [ ] 验证 tmux 分屏
- [ ] 验证 htop 实时刷新
- [ ] 退出 vim 后界面恢复正常（alt screen 切换）
- [ ] 性能调优（QPainter 批量操作、减少不必要的重绘）

### 阶段 6：高级功能 ✅ 检查点 #6

- [ ] 文本选择和复制（鼠标拖选 → QClipboard）
- [ ] 滚动回看历史
- [ ] 右键菜单
- [ ] Windows 平台支持（`par-term-emu-core-rust` 已内置，主要验证）

---

## 8. 检查点清单（精简版）

### 🔵 检查点 #0：项目初始化
**验证条件**：
- `uv sync` 无报错
- `from par_term_emu_core_rust import PtyTerminal` 成功
- `python main.py` 启动空 PySide6 窗口

### 🔵 检查点 #1：基础渲染
**验证条件**：
- 窗口显示等宽字符网格
- resize 窗口时行列数正确更新
- 手动调用 `term.process_str("Hello\nWorld")` 后正确渲染

### 🔵 检查点 #2：PTY 集成
**验证条件**：
- 启动 bash/zsh，显示提示符
- 输入 `ls` 能看到输出
- 窗口 resize 后，`stty size` 显示正确的行列数
- 增量渲染工作正常（只重绘脏行）

### 🔵 检查点 #3：escape 序列渲染
**验证条件**：
- `echo -e "\x1b[31mRED\x1b[0m"` 显示红色文字
- `ls --color` 颜色正常
- 光标可见且闪烁

### 🔵 检查点 #4：键盘输入
**验证条件**：
- 方向键在 bash 中正常工作
- `nano` 可以启动和基本操作

### 🔵 检查点 #5：复杂 TUI
**验证条件**：
- `vim` 正常显示（语法高亮、分屏、模式切换）
- `htop` 正常显示和操作
- 退出 vim 后界面恢复正常

### 🔵 检查点 #6：高级功能
**验证条件**：
- 鼠标拖选文字可复制
- 滚动回看历史内容
- （Windows）基本功能正常

---

## 9. 风险与待确认事项

### 9.1 已知风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| par-term-emu-core-rust 社区较小 | 遇到 bug 时难以获得帮助 | 源码公开(MIT)，可提 issue；内部解析器是成熟的 vte crate |
| Rust 引擎 API 可能有未被文档覆盖的行为 | 集成时遇到接口问题 | 先写简单 POC 验证核心 API，发现问题及时调整 |
| Python 3.12+ 限制 | 某些环境可能不满足 | uv 轻松管理版本，非问题 |
| Beta 状态 | 可能有隐藏 bug | 实际测试核心场景（vim/nano/bash）验证稳定性 |
| Windows PTY 行为差异 | Windows 兼容性问题 | 阶段 6 再处理，有时间窗口 |

### 9.2 已确认事项 ✅

1. ✅ **Python 版本**：3.12.13，通过 `uv python install 3.12.13` 已安装
2. ✅ **解析引擎**：`par-term-emu-core-rust` v0.42.2，预编译 wheel
3. ✅ **Windows**：阶段 6 再处理
4. ✅ **架构**：Rust 引擎 + QPainter Widget + InputHandler
5. ✅ **True Color**：Rust 引擎完整支持，无需额外处理

---

## 附录 A：项目结构

```
terminal/
├── pyproject.toml              # uv 项目配置 (Python 3.12+)
├── main.py                     # QApplication + TerminalWidget
├── DESIGN.md                   # 本文件
├── ERRORS.md                   # 错误记录
├── terminal/
│   ├── __init__.py
│   ├── widget.py               # TerminalWidget (QPainter 渲染)
│   └── input_handler.py        # 键盘输入编码
└── tests/
    ├── test_widget.py
    └── test_input_handler.py
```

## 附录 B：关键参考资料

- [par-term-emu-core-rust GitHub](https://github.com/paulrobello/par-term-emu-core-rust) — Rust 引擎源码和示例
- [par-term-emu-core-rust PyPI](https://pypi.org/project/par-term-emu-core-rust/) — 最新版本信息
- [xterm.js 源码](https://github.com/xtermjs/xterm.js) — 架构参考
- [QTermWidget 源码](https://github.com/lxqt/qtermwidget) — QPainter 渲染参考 (C++)
- [VT100 用户手册](https://vt100.net/docs/vt100-ug/)
- [Paul Williams' VT100 Parser FSM](https://vt100.net/emu/dec_ansi_parser)
