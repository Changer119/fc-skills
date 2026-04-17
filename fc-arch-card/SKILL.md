---
name: fc-arch-card
description: |
  接收自然语言描述，输出技术架构图（PNG，可选 SVG）。支持 4 种视觉风格（工程极简、现代设计、暗黑、彩色自定义）和 2 种图表类型（系统架构图、流程图/时序图）。
  触发场景：用户说"画架构图"、"画流程图"、"画系统图"、"生成架构图"等。
  示例：画一个包含 API Gateway、三个微服务和 Redis 的系统架构图 -m
metadata:
  clawdbot:
    emoji: "📐"
    requires:
      bins: ["uv"]
---

# fc-arch-card - 技术架构图生成

接收自然语言描述，输出专业风格的技术架构图。

## 使用方式

```bash
# 系统架构图（默认风格：工程极简）
/fc-arch-card 画一个电商系统架构，包含网关、用户服务、订单服务、MySQL 和 Redis

# 指定现代设计风格
/fc-arch-card 画一个微服务架构 -m

# 暗黑风格流程图
/fc-arch-card 画用户登录流程图 -f -d

# 输出 SVG 额外格式
/fc-arch-card 画一个推荐系统架构 -c -svg
```

## 参数说明

| 参数 | 含义 | 默认 |
|------|------|------|
| `-a` | 系统架构图 | ✓ |
| `-f` | 流程图/时序图 | |
| `-e` | 工程极简风格 | ✓ |
| `-m` | 现代设计感 | |
| `-d` | 暗黑风 | |
| `-c` | 彩色自定义 | |
| `-svg` | 额外输出 SVG | |

## 工作流程

```
用户输入 → 解析参数 → 读取配置 → 生成 Mermaid DSL
    → 填充模板 → 启动服务 → Playwright 截图 → 输出 PNG
    → [失败] → 降级手写 SVG → 重新截图
```

## 输出位置

图表保存至 `~/Downloads/{name}.png`：
- `{name}` 根据图表内容自动生成（英文小写，连字符连接）
- 如带 `-svg` 参数，同时输出 `~/Downloads/{name}.svg`

## 风格预览

| 参数 | 风格 | 适用场景 |
|------|------|----------|
| `-e` | 工程极简 | 技术文档、RFC、架构评审 |
| `-m` | 现代设计感 | 产品演示、设计稿 |
| `-d` | 暗黑风 | 深色模式文档、监控大屏 |
| `-c` | 彩色自定义 | 教学演示、博客配图 |

## 实现细节

### 渲染流程

1. **参数解析**：提取图表类型、风格、输出格式
2. **读取配置**：从 references/ 读取风格变量和执行步骤
3. **生成 DSL**：LLM 根据描述生成 Mermaid 语法
4. **填充模板**：将 DSL 和主题变量注入 template.html
5. **启动服务**：render_server.py 在本地端口提供服务
6. **Playwright 截图**：capture.py 访问页面并截图
7. **降级处理**：Mermaid 失败时，LLM 生成手写 SVG 重新渲染

### 文件结构

```
fc-arch-card/
├── SKILL.md              # 本文件（路由器）
├── requirements.txt      # playwright 依赖
├── scripts/
│   └── run.sh            # 依赖安装脚本
└── assets/
    ├── capture.py        # Playwright 截图
    ├── render_server.py  # 本地 HTTP 服务
    └── template.html     # Mermaid 模板

references/
├── taste.md              # 视觉质量约束
├── themes.md             # 4 种风格配置
├── mode-arch.md          # 架构图步骤
└── mode-flow.md          # 流程图步骤
```

## 依赖

- Python 3.10+
- Playwright (Python)
- Chromium 浏览器（Playwright 自动安装）

安装命令：
```bash
uv add playwright
uv run playwright install chromium
```

## 注意事项

- **Mermaid 语法错误**：会自动降级为手写 SVG 重新渲染
- **节点数量限制**：建议不超过 20 个节点以保持可读性
- **命名规范**：自动生成的文件名使用英文小写和连字符
