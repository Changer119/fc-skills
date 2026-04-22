---
name: fc-skill-sync
description: Use when需要同步多个技能目录中的skills，确保skills在~/.openclaw/skills、~/.claude/skills和~/.agents/skills三个目录中保持一致，通过软链接管理避免重复存储
---

# fc-skill-sync

## Overview

同步三个技能目录（`~/.openclaw/skills`、`~/.claude/skills`、`~/.agents/skills`）中的所有 skills。确保每个 skill 只存储一份实体文件，其他目录通过软链接引用，避免重复和版本不一致。

## When to Use

- 需要在一个目录中使用其他目录已存在的 skill
- 执行同步操作确保所有 skills 在三目录中可用
- 整理或迁移 skills 后需要重新同步
- 检测到 skill 版本不一致需要重新建立软链接

## Core Pattern

**单实体 + 多链接模式：**

```
~/.claude/skills/my-skill/SKILL.md     ← 实体文件（以第一个找到的为准）
~/.openclaw/skills/my-skill/SKILL.md   ← 软链接 → ~/.claude/skills/my-skill
~/.agents/skills/my-skill/SKILL.md     ← 软链接 → ~/.claude/skills/my-skill
```

## Quick Reference

| 操作 | 命令 |
|------|------|
| 执行同步 | `claude /fc-skill-sync` |
| 查看同步结果 | 检查输出报告 |

## 同步规则

1. **扫描阶段**：遍历三个目录，收集所有 skill 名称
2. **确定实体**：对于每个 skill，以第一个找到实体文件的目录为准
3. **创建链接**：在其他目录创建指向实体目录的软链接
4. **冲突处理**：如果某目录已存在同名但非链接的文件/目录，备份为 `.backup.{timestamp}`

## 执行流程

```bash
# 1. 确保三个目录存在
mkdir -p ~/.openclaw/skills ~/.claude/skills ~/.agents/skills

# 2. 收集所有 skills
find ~/.openclaw/skills ~/.claude/skills ~/.agents/skills -maxdepth 1 -type d

# 3. 对每个 skill：
#    - 检查哪个目录有实体（非软链接）
#    - 在其他目录创建/更新软链接
#    - 处理冲突（备份现有非链接文件）
```

## Common Mistakes

| 错误 | 后果 | 修复 |
|------|------|------|
| 手动复制 skill 文件 | 版本不一致，更新困难 | 删除副本，运行同步建立软链接 |
| 删除实体目录 | 所有软链接失效 | 从备份恢复或重新安装 skill |
| 修改软链接指向 | 同步后会被覆盖 | 直接修改实体文件 |

## Implementation

使用配套脚本执行同步：

```bash
bash ~/.claude/skills/fc-skill-sync/sync-skills.sh
```

脚本功能：
- 自动检测三个目录中的 skills
- 保持实体文件唯一性
- 创建或更新软链接
- 备份冲突文件
- 生成同步报告
