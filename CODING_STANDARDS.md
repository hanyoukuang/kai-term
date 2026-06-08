# pyqterminal — 编程规范文档

> **目标受众**：人类开发者 + AI Agent  
> **创建日期**：2026-06-08  
> **适用范围**：本项目所有代码、文档改动必须遵守本规范。

---

## 目录

1. [通用行为规则](#1-通用行为规则)
2. [Python 语言规范 (PEP 8)](#2-python-语言规范-pep-8)
3. [代码拆分规范](#3-代码拆分规范)
4. [注释规范](#4-注释规范)
5. [代码实现规范](#5-代码实现规范)
6. [外部库使用规范](#6-外部库使用规范)
7. [项目特定规范](#7-项目特定规范)
8. [日志规范](#8-日志规范)
9. [测试规范](#9-测试规范)
10. [Git 工作流](#10-git-工作流)

---

## 1. 通用行为规则

### 1.1 不确定时，停下来

> 无论何时，拿不定主意的时候，直接通知用户。不要猜测。

遇到以下情况必须询问：
- 需求有多种实现方式，且各有显著优劣
- 实现难度评估后发现风险过大
- 无法确定用户意图（歧义）
- 代码改动可能引入不可预见的副作用

### 1.2 先分析，再动手

解决问题前必须：
1. 写出思考步骤和分析过程
2. 评估可行性（实现难度、风险、工期）
3. 若难度过大，通知用户而非硬上
4. 确认方案后再写代码

### 1.3 歧义消除

用户提示词有歧义时，需及时询问。按以下步骤：
1. 明确列出你对用户需求的理解
2. 指出歧义点
3. 给出选项供用户选择
4. **避免返工比赶进度更重要**

### 1.4 失败处理升级链

问题难以解决或多次尝试失败后，按优先级考虑：

1. **只考虑本项目代码**（不含外部库）：代码间影响、边界问题、逻辑漏洞 → 反思或向用户反馈
2. **搜索相同或类似问题的解法**（网络搜索）
3. **换一种思考方式**（换个角度切入）
4. **判断是否为外部库边界**：若功能处于外部库架构边界，库未考虑此情况 → 直接反馈用户

### 1.5 上下文压缩规则

压缩上下文时，除必要信息外还需追加：
1. 重要代码、边界条件的处理原理
2. 编译器或解释器的警告、报错
3. 存在的逻辑漏洞、代码实现问题
4. 已发现但来不及处理的问题
5. 其它值得追加的信息

若追加内容仍不能有效缓解上下文压力，只保留必要消息，追加内容记录在 markdown 文件中。

---

## 2. Python 语言规范 (PEP 8)

### 2.1 基本原则

- 严格遵循 [PEP 8](https://peps.python.org/pep-0008/) 规范
- 使用 4 空格缩进（不允许 tab）
- 行宽限制：**100 字符**（该项目放宽至 100，因 PySide6 API 调用常含长参数列表）
- 编码声明：Python 3 默认 UTF-8，无需 `# -*- coding: utf-8 -*-`

### 2.2 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块/包 | lowercase_with_underscores | `terminal_widget.py` |
| 类 | PascalCase | `TerminalWidget` |
| 函数/方法 | lowercase_with_underscores | `_poll_updates()` |
| 私有成员（内部） | `_single_leading_underscore` | `_term`, `_cell_w` |
| 私有成员（名称改编） | `__double_leading_underscore` | `__internal_cache` |
| 常量 | UPPER_CASE_WITH_UNDERSCORES | `DEFAULT_FG`, `_FONT_CANDIDATES` |
| 变量 | lowercase_with_underscores | `scroll_offset` |

### 2.3 导入顺序

```
1. 标准库
2. 第三方库
3. 项目内部模块

每组之间空一行，字母顺序排列。
```

示例：
```python
import sys
import logging

from par_term_emu_core_rust import PtyTerminal
from PySide6.QtWidgets import QWidget

from .input_handler import InputHandler
from .theme import _pick_monospace_font, _FONT_CANDIDATES
```

### 2.4 类型注解

- 所有公开 API 必须有类型注解
- 内部方法鼓励类型注解（至少参数类型）
- 使用 Python 3.10+ 风格：`list[tuple]`, `str | None`

```python
def encode(cls, event: QKeyEvent) -> bytes | None:  # ✅
def encode(cls, event):                              # ❌
```

---

## 3. 代码拆分规范

### 3.1 文件行数限制

- **单个文件不超过 500 行**（特殊情况可放宽至 600 行）
- 超过限制时：提取独立类/函数到新模块
- 当前 `widget.py` (1088 行) 是已知超标项，逐步拆分中

### 3.2 函数/方法行数限制

- **类、函数、方法不超过 50 行**（特殊情况可放宽至 80 行）
- 超过 50 行时：提取子方法或辅助函数
- 例外：`_render_cells()` 等核心渲染循环因逻辑连贯性可放宽至 120 行

### 3.3 单一职责

- 类、函数、方法只需知道实现其功能所需的信息
- 禁止传递不需要的参数，禁止方法访问不需要的成员变量
- 拆分时可以接受一定的代码重复（避免过度耦合）

### 3.4 模块职责划分

| 模块 | 职责 | 预计行数 |
|------|------|----------|
| `terminal/widget.py` | 主 Widget：渲染调度、事件分发 | < 600 |
| `terminal/input_handler.py` | 键盘编码 | ~110 |
| `terminal/background_propagator.py` | 背景色传播预处理 | ~80 |
| `terminal/block_chars.py` | Unicode 块字符绘制 | ~60 |
| `terminal/theme.py` | 字体选择、默认颜色 | ~30 |

---

## 4. 注释规范

### 4.1 类、方法、变量注释

- 公开类必须有 docstring（描述作用和用法）
- 公开方法必须有 docstring（描述参数、返回值、副作用）
- 内部方法鼓励 docstring（至少一行概述）
- **有特殊功能的变量一定要注释**（如状态标志位、缓存、计数器）

```python
class TerminalWidget(QWidget):
    """PySide6 terminal emulator widget.

    Two operating modes:
      - Interactive mode (default): spawns a shell via PTY
      - Display-only mode (display_only=True): feed escape sequences via feed()

    Renders directly in paintEvent() via QPainter — no QPixmap double-buffer.
    """
```

### 4.2 状态机注释

- 必须写明状态机的流程
- 状态改变的条件
- 各个状态对应的控制变量值

```python
# Selection state machine:
#   idle              — _sel_start=None, _sel_end=None, _selecting=False
#   drag_detected     — mouse moved >= 1px → _selecting=True
#   selecting         — mouse moving with _selecting=True, updates _sel_end
#   released(w/text)  — copies to clipboard, keeps selection visible
#   released(no text) — _clear_selection(), back to idle
#   cleared_on_key    — keyboard input → _clear_selection(), back to idle
```

### 4.3 潜在 bug 点注释

- 可能触发 bug 的写法必须注释（尤其是经过了多次试错的修复）
- 标注"禁止修改"的关键代码段和原因

```python
# ⚠️  DO NOT reorder: background fill MUST precede space-skip.
# See ERRORS.md #6 — spaces with colored backgrounds were invisible.
```

### 4.4 注释风格

- sphinx-style docstring 不强制（但公开 API 推荐）
- 中文注释可用在内部方法中，公开 API 注释用英文
- 行内注释与代码至少空 2 格

---

## 5. 代码实现规范

### 5.1 语法糖与语言特性

- 在不影响可读性、版本兼容的情况下，可使用语法糖
- 优先使用语言特性以提高性能或安全性（如 `match-case`、`walrus operator`）

### 5.2 实现优先级链

实现功能时，按以下优先级检查：

```
1. 标准库是否提供解决方案                    （最高优先级）
2. 已引入的外部库是否有相同或类似功能
3. 功能难以实现或易出错时，可考虑未引入的外部库
4. 其他可靠的外部实现方法
5. 自行实现（滚轮子）                        （最低优先级）
```

#### 5.2.1 自行实现的要求

评估后确实需要自行实现时：

1. **代码实现尽可能简单**，杜绝炫技
2. **易于调试 bug**，排错方便
3. **阅读者心智负担低**（agent 和人类均如此）
4. 能够处理正常、边界、非法三种情况（normal/boundary/error）
5. 非法情况能触发异常并被捕获
6. 不会与其他功能冲突（如两个方法修改同一变量导致状态混乱）

### 5.3 边界与错误处理

- 所有外部输入必须有边界检查
- 所有异常必须被捕获并记录日志（见 [日志规范](#8-日志规范)）
- 禁止吞掉异常（空 `except:` 或 `except: pass`）
- 禁止使用 `as any`, `@ts-ignore`, `@ts-expect-error` 压制类型错误

```python
# ❌ 禁止
except:
    pass

# ✅ 正确
except Exception:
    _log.exception("operation failed")
    return fallback_value
```

### 5.4 禁止事项

| 禁止 | 说明 |
|------|------|
| `as any`, `@ts-ignore`, `@ts-expect-error` | 压制类型错误 |
| `except: pass` 或空 `except:` | 吞掉异常 |
| 删除失败测试来"通过" | 作弊 |
| 猜测未读的代码 | 必须实际读取 |
| 修复失败 3 次后继续尝试 | 必须停下并咨询 |

---

## 6. 外部库使用规范

### 6.1 库选择优先级

1. **优先选择久经考验的成熟库**
2. 其次考虑功能多、文档完善、社区活跃、速度快的新库

### 6.2 库比较维度

库太少时，按以下顺序综合考虑：

1. **兼容性**：跨平台、多设备性好，与项目中其他库不冲突
2. **架构质量**：在 GitHub issues、项目文档中查找缺陷，确认不影响目标功能
3. **性能**：满足用户需求
4. **功能完备度**：自行实现的工作量小
5. **文档/API 完善度**
6. **代码现代化、可读性**

### 6.3 局限性透明

- 若借助库不能实现所有功能，必须明确提示
- 必须征求用户意见后再决定方向
- 避免被库瓶颈卡住

### 6.4 不熟悉的外部库

- 必须阅读 API 文档，掌握类、方法、函数的功能
- 必要时搜索可靠的用法示例
- 评估库是否完全满足需求

### 6.5 本项目外部库

| 库 | 版本 | 用途 | 关键注意事项 |
|----|------|------|-------------|
| `par-term-emu-core-rust` | ≥0.42.3 | VT520 解析 + PTY | 见 ERRORS.md 陷阱备忘录 |
| `PySide6` | ≥6.11.1 | Qt 前端渲染 | 见 ERRORS.md Qt 陷阱 |
| `pytest` | ≥9.0.3 | 测试框架 | 仅 dev 依赖 |

---

## 7. 项目特定规范

### 7.1 关键 API 陷阱（必读）

> 来自 ERRORS.md。**操作 widget.py 前必须阅读。**

| 期望（错误） | 实际 |
|---|---|
| `get_cell_char(row, col)` | `get_line_cells(row)` 返回 `list[(char, fg, bg, attrs), ...]` |
| `damage_regions_since(gen)` | 不使用。改用 `has_updates_since(gen)` + `update_generation()` |
| `process_str()` on PtyTerminal | 仅存在于 headless `Terminal`，不在 PtyTerminal 上 |
| 整型 cursor style | `cursor_style()` 返回 `CursorStyle` 枚举 |
| `write_str()` takes bytes | `write_str()` 接收 `str`，`write()` 接收 `bytes` |
| `resize(rows, cols)` | 代码调用 `_term.resize(self._cols, self._rows)` 即 `(cols, rows)` 顺序 |

### 7.2 渲染规则（禁止私自改动）

来自 `_render_cells()` 的硬编码规则（历经多次试错确定）。

1. **背景填充在空格检查之前**：见 `widget.py` 中的 `⚠️ DO NOT reorder` 注释
2. **不使用 QPixmap 双缓冲**：因 Retina/HiDPI 问题（ERRORS.md #5）已移除
3. **Reverse video (SGR 7)**：Rust 引擎不预交换 fg/bg，渲染层负责
4. **Hidden text (SGR 8)**：只显示背景，跳过文字
5. **Wide chars (CJK)**：宽字符占 2 列，spacer 单元格需完全跳过
6. **Blink (SGR 5)**：用 `_blink_visible` 控制闪烁阶段

### 7.3 平台差异

| 行为 | macOS | Linux | Windows |
|------|-------|-------|---------|
| Ctrl 键映射 | `Qt.MetaModifier` (Cmd) | `Qt.ControlModifier` | `Qt.ControlModifier` |
| 复制快捷键 | Cmd+C (Ctrl only) | Ctrl+Shift+C | Ctrl+Shift+C |
| 粘贴快捷键 | Cmd+V (Ctrl only) | Ctrl+Shift+V | Ctrl+Shift+V |
| 缩放快捷键 | Ctrl++/-/0 | Ctrl+Shift++/-/0 | Ctrl+Shift++/-/0 |
| has_updates_since | 可靠 | 可靠 | 不可靠（回退到光标检查） |

---

## 8. 日志规范

### 8.1 每个异常必须有日志

```python
# ✅
try:
    self._term.spawn_shell()
except Exception:
    _log.exception("spawn_shell failed")  # 自动包含 traceback

# ❌
except Exception:
    pass
```

### 8.2 重要运行状态记录

| 事件 | 日志级别 |
|------|----------|
| PTY shell 启动成功/失败 | `INFO` / `ERROR` |
| 窗口 resize（行列数变化） | `DEBUG` |
| 字体大小改变 | `DEBUG` |
| Alt Screen 切换 | `DEBUG` |
| process_exited 信号发出 | `WARNING` |
| paintEvent 异常 | `ERROR` |
| keyPressEvent 异常 | `ERROR` |
| 鼠标事件异常 | `ERROR` |
| OSC 通知桥接 | `DEBUG` |

### 8.3 日志格式

当前默认格式（来自 `__main__.py`）：
```
%(asctime)s [%(name)s] %(levelname)s: %(message)s
```

模块级 logger：
```python
import logging
_log = logging.getLogger(__name__)
```

---

## 9. 测试规范

### 9.1 测试数据要求

每个测试必须包含三类数据：

| 类别 | 说明 | 预期 |
|------|------|------|
| **正常数据** | 典型的合法输入 | 正常输出或功能执行 |
| **边界数据** | 极限值、空值、单元素、最大值 | 正常输出或功能执行 |
| **错误数据** | 非法输入、类型不匹配、越界 | 触发异常并被捕获 |

### 9.2 测试文件命名

```
tests/
├── test_<module>.py       # 单元测试
├── <name>_visual_test.py  # 视觉验证（需手动运行）
└── *.sh                   # 终端转义序列冒烟测试
```

### 9.3 测试配置

`pytest.ini` 已配置：
```ini
[pytest]
testpaths = tests
python_files = test_*.py
```

---

## 10. Git 工作流

### 10.1 提交粒度

- 每完成一个独立阶段（功能模块、文档更新等）提交一次
- 提交信息格式：`<类型>: <描述>`
  - `feat:` 新功能
  - `fix:` 修复
  - `docs:` 文档
  - `refactor:` 重构
  - `test:` 测试
  - `style:` 格式调整

### 10.2 提交前检查

- [ ] 移除历史遗留代码
- [ ] 更新相关文档
- [ ] 更新相关注释
- [ ] 确认 `uv run python main.py` 可正常启动

### 10.3 推送到远端

- **仅用户明示后**才推送到远端仓库
- 默认只在本地提交

---

## 附录 A：文档索引

| 文档 | 受众 | 内容 |
|------|------|------|
| `README.md` | 人类 + AI | 项目概述、安装、使用 |
| `API.md` | 人类 + AI | API 参考 |
| `AGENTS.md` | AI | 项目架构、关键 API 陷阱、渲染规则 |
| `DESIGN.md` | 人类 + AI | 架构设计、技术决策 |
| `ERRORS.md` | 人类 + AI | 错误历史、陷阱备忘录 |
| `CHANGELOG.md` | 人类 | 版本历史 |
| `HISTORY.md` | 人类 + AI | 外部库改动历史、类/方法改动历史 |
| `CODING_STANDARDS.md` | 人类 + AI | 本文件 |

---

## 附录 B：相关资源

- [PEP 8 — Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [PySide6 Documentation](https://doc.qt.io/qtforpython-6/)
- [par-term-emu-core-rust GitHub](https://github.com/paulrobello/par-term-emu-core-rust)
- [alacritty vte crate](https://crates.io/crates/vte)
- [xterm.js Architecture](https://github.com/xtermjs/xterm.js)
