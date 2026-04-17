# fc-arch-card Skill 设计文档

**日期：** 2026-04-17  
**状态：** 已确认，待实现

---

## 概述

一个 Claude Code skill，接收自然语言描述，输出技术架构图（PNG 默认，可选 SVG）。底层使用 Mermaid 渲染，Playwright 截图，Mermaid 失败时降级为手写 SVG 重新截图。

---

## 触发条件

当用户说"画架构图"、"画流程图"、"画系统图"、"生成架构图"等类似表达时触发。

---

## 参数

| 参数 | 含义 | 默认 |
|------|------|------|
| `-a` | 系统架构图（节点+连线+分层） | ✓ |
| `-f` | 流程图 / 时序图 | |
| `-e` | 风格：工程极简 | ✓ |
| `-m` | 风格：现代设计感 | |
| `-d` | 风格：暗黑风 | |
| `-c` | 风格：彩色自定义 | |
| `-svg` | 额外输出 SVG（默认只输出 PNG） | |

**示例：**
```
/fc-arch-card 画一个包含 API Gateway、三个微服务和 Redis 的系统架构图 -m
/fc-arch-card 画用户注册的完整流程图 -f -d -svg
```

---

## 输出位置

- PNG: `~/Downloads/{name}.png`
- SVG（如带 `-svg`）: `~/Downloads/{name}.svg`

`{name}` 由 LLM 根据图表内容自动生成（英文小写，单词间用连字符，如 `microservice-architecture`）。

---

## 技术选型

| 组件 | 选择 | 理由 |
|------|------|------|
| 浏览器自动化 | Python Playwright | 遵循项目 Python/uv 规范 |
| Mermaid 渲染 | Chromium 无头浏览器 | Playwright 内置支持 |
| 本地服务 | Python http.server | 无需额外依赖 |
| 降级方案 | LLM 手写 SVG | 统一视觉风格 |

---

## 目录结构

```
~/.claude/skills/fc-arch-card/
├── SKILL.md                   ← 路由器（Python 实现）
├── requirements.txt           ← playwright 依赖
├── assets/
│   ├── capture.py             ← 截图工具
│   ├── render_server.py       ← 本地 HTTP 渲染服务
│   └── template.html          ← Mermaid 渲染容器
└── references/
    ├── taste.md               ← 视觉质量底线
    ├── themes.md              ← 4 种风格的 CSS 变量
    ├── mode-arch.md           ← 系统架构图执行步骤
    └── mode-flow.md           ← 流程图/时序图执行步骤
```

---

## 渲染管道

```
自然语言输入
    ↓
[1] 解析参数（图类型 + 风格 + 输出格式）
    ↓
[2] Read taste.md + themes.md
    ↓
[3] Read mode-arch.md 或 mode-flow.md（按图类型分派）
    ↓
[4] LLM 根据内容生成 Mermaid DSL
    ↓
[5] 注入 template.html → 启动 render_server.py
    ↓
[6] capture.py 截图 → ~/Downloads/{name}.png
    ↓
[7] 如带 -svg 参数 → 提取 SVG → ~/Downloads/{name}.svg
    ↓
[8] 如 Mermaid 渲染失败 → 降级：LLM 生成手写 SVG → 重新截图
```

---

## template.html 核心结构

```html
<!DOCTYPE html>
<html>
<head>
  <style>
    body { margin: 0; background: {{BG_COLOR}}; font-family: {{FONT_FAMILY}}; }
    .diagram-wrapper { padding: 48px; display: flex; justify-content: center; }
  </style>
</head>
<body>
  <div class="diagram-wrapper">
    <pre class="mermaid">
%%{init: {{MERMAID_THEME_CONFIG}}}%%
{{MERMAID_DSL}}
    </pre>
  </div>
  <script src="mermaid.min.js"></script>
  <script>mermaid.initialize({ startOnLoad: true });</script>
</body>
</html>
```

**模板变量：**

| 变量 | 来源 |
|------|------|
| `{{MERMAID_THEME_CONFIG}}` | themes.md 对应风格的 JSON |
| `{{MERMAID_DSL}}` | LLM 根据自然语言生成 |
| `{{BG_COLOR}}` | themes.md 对应风格的背景色 |
| `{{FONT_FAMILY}}` | themes.md 对应风格的字体 |

---

## 4 种风格主题

### `-e` 工程极简（默认）
- 背景：`#FFFFFF`
- 节点：白底 + 细边框 `#333333`
- 连线：`#666666`，细线
- 字体：`JetBrains Mono, monospace`
- 气质：C4 模型、RFC 文档风格

### `-m` 现代设计感
- 背景：`#F8F9FC`（暖白）
- 节点：圆角卡片，主色 `#3B5BDB`（靛蓝），带染色阴影
- 连线：跟随主色，带箭头样式
- 字体：`Geist, sans-serif`
- 气质：Figma 社区架构图风格

### `-d` 暗黑风
- 背景：`#1A1A2E`（深海蓝黑）
- 节点：`#16213E`，高亮边框 `#0F3460`，文字 `#E0E0E0`
- 连线：`#00B4D8`（青色高亮）
- 字体：`JetBrains Mono, monospace`
- 气质：终端、监控大屏风格

### `-c` 彩色自定义
- 背景：`#FAFAFA`
- 节点：按层级/类型自动分配色块（网关橙、服务蓝、存储绿、队列紫）
- 连线：颜色区分同步/异步调用
- 字体：`Outfit, sans-serif`
- 气质：彩色技术博客配图风格

**themes.md 数据格式（每种风格一个区块）：**
```markdown
## engineering (-e)
BG_COLOR: #FFFFFF
FONT_FAMILY: JetBrains Mono, monospace
MERMAID_THEME: base
MERMAID_VARS: {"primaryColor":"#FFFFFF","primaryBorderColor":"#333333",...}
```

---

## mode-arch.md 执行步骤（系统架构图）

1. **理解输入** — 识别组件（服务、存储、网关、客户端）、连接关系、分层逻辑
2. **生成 Mermaid DSL** — 使用 `graph TD` 或 `graph LR`；按层级用 `subgraph` 分组；节点命名简洁
3. **DSL 自检** — 节点 ≤ 20 个；subgraph ≤ 3 层；语法正确
4. **填模板** — 注入 DSL + 主题变量 → 启动本地服务
5. **截图** — capture.py 输出 PNG，可选 SVG

**生成约束：**
- 架构图必须有明确数据流方向（箭头方向表达）
- 同类组件放同一 subgraph
- 节点 label 中英文保持统一，不混用
- 禁止所有节点平铺无分组

---

## mode-flow.md 执行步骤（流程图 / 时序图）

1. **判断子类型** — 多参与者交互 → `sequenceDiagram`；单线流程 → `flowchart TD`
2. **生成 Mermaid DSL** — 流程图标注判断节点（菱形）；时序图标注同步/异步消息
3. **DSL 自检** — 步骤 ≤ 15 个；时序图参与者 ≤ 6 个
4. **填模板** → 截图

**生成约束：**
- 流程图必须有明确开始和结束节点
- 判断分支必须标注条件（`是/否` 或 `success/fail`）

---

## capture.py 关键逻辑

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(f"http://localhost:{port}/template.html")
    
    # 等待 Mermaid 渲染完成
    page.wait_for_selector(".mermaid svg", timeout=10000)
    
    # 降级检测
    error = page.query_selector(".mermaid .error-icon")
    if error:
        browser.close()
        return "RENDER_FAILED"
    
    # PNG 截图
    page.screenshot(path=png_file, full_page=True)
    
    # SVG 提取（-svg 模式）
    if output_svg:
        svg_content = page.eval_on_selector(".mermaid svg", "el => el.outerHTML")
        with open(svg_file, "w") as f:
            f.write(svg_content)
    
    browser.close()
```

---

## taste.md 核心原则（架构图专用）

- 禁止节点标签超过 20 字符（保持简洁）
- 禁止无方向的连线（每条线必须有箭头）
- 禁止超过 3 层 subgraph 嵌套（增加理解难度）
- 连线上的标注文字 ≤ 10 字符
- 输出图宽度固定 1080px，高度自动撑开

---

## 降级策略（Mermaid 渲染失败时）

当 Mermaid 语法解析失败（检测到 `.mermaid .error-icon`）：

1. **触发降级**：capture.py 返回 `RENDER_FAILED`
2. **LLM 生成手写 SVG**：根据原始描述生成完整 SVG XML
3. **重新渲染**：将手写 SVG 注入新模板 → 启动服务 → capture.py 截图
4. **输出**：保持与其他模式相同的 PNG/SVG 输出

降级后的 SVG 同样遵循所选主题的配色和字体规范。

---

## 依赖

- Python 3.10+
- Playwright (Python)
- Chromium 浏览器（Playwright 自动安装）

**安装命令：**
```bash
uv add playwright
uv run playwright install chromium
```

---

## 未决问题

无。

---

## 实施顺序建议

1. `assets/capture.py`（核心截图工具）
2. `assets/render_server.py`（本地 HTTP 服务）
3. `assets/template.html`（渲染容器）
4. `references/themes.md`（4 种风格变量）
5. `references/taste.md`（质量约束）
6. `references/mode-arch.md`（系统架构图步骤）
7. `references/mode-flow.md`（流程图步骤）
8. `SKILL.md`（路由器）
9. `requirements.txt` + 测试安装
