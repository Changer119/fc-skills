---
name: fc-save2obsidian-skill
description: |
  将当前 Claude Code 会话中最近若干轮对话内容，保存为 Markdown 笔记写入 Obsidian second-brain 知识库。
  触发场景：用户说"保存到obsidian"、"存到知识库"、"把这次对话记录下来"、"把刚才的结果存一下"等。
  支持参数 N：保存最近 N 轮对话（一轮 = 一次用户提问 + 一次 Claude 回复），不传则默认 N=1（仅最近一轮）。
  示例：/fc-save2obsidian-skill 、 /fc-save2obsidian-skill 3
metadata:
  clawdbot:
    emoji: "🗂️"
    requires:
      bins: ["obsidian"]
---

# fc-save2obsidian-skill - 保存对话到 Obsidian

将当前会话最近 N 轮对话整理为一篇 Markdown 笔记，通过 `obsidian` CLI 写入 Obsidian second-brain vault。

## 使用方式

```bash
/fc-save2obsidian-skill        # 保存最近 1 轮对话
/fc-save2obsidian-skill 3      # 保存最近 3 轮对话
```

## 执行步骤

### 1. 确定保存轮数 N

- 用户传入了数字参数 → N = 该数字
- 未传参数 → N = 1
- "一轮"指：一次用户提问（含上下文消息）+ 对应的一次 Claude 完整回复（包括关键的工具调用结果摘要，但不包含冗长的中间日志）

### 2. 提取对话内容

从当前会话上下文中，回溯提取最近 N 轮的：

- 用户的原始提问/指令
- Claude 的最终回复内容（文字说明 + 关键产出，如代码改动摘要、生成的文件路径、结论等）
- 如果某轮涉及生成的文件、链接、命令执行结果等关键产物，需在笔记中保留引用（路径或链接），不要照抄大段日志

### 3. 整理成 Markdown 笔记

按以下结构组织内容，遵循 **obsidian-markdown** skill 的格式规范：

```markdown
---
title: <根据对话主题自动生成的标题>
tags: [Claude会话, <按内容补充的1-2个主题标签>]
created: <今天日期 YYYY-MM-DD>
source: claude-code-session
---

# <标题>

## 第 1 轮

### 提问
<用户原始问题，可适当精简>

### 回复
<Claude 的回答要点 / 产出>

## 第 2 轮
...（如 N > 1，依次列出每一轮）
```

- 标题：根据对话核心主题用一句话概括，不要使用"对话记录"这类无信息量的词
- 多轮之间用 `## 第 N 轮` 二级标题分隔，保持时间顺序（从早到晚）
- 内容较长时做摘要，保留关键代码片段、文件路径、结论；避免整段粘贴工具调用的原始输出

### 4. 写入 Obsidian

默认写入 `~/Obsidian/second-brain/Claude会话记录/` 目录。

写入前先检查同名文件是否已存在：

```bash
obsidian search query="file:<标题>"
```

| 情况 | 处理 |
|------|------|
| 文件不存在 | `obsidian create name="Claude会话记录/<标题>" content="<整理后的笔记内容>" silent` |
| 文件已存在 | 询问用户：覆盖 / 追加 / 另存为新文件 |

文件命名遵循 obsidian-write 规范：中文标题保留中文，空格转下划线；可加日期前缀，如 `2026-06-10-技能开发讨论.md`。

## 完成后告知用户

- 笔记完整路径（相对 vault 根目录）
- 保存了几轮对话
- 一句话内容摘要
