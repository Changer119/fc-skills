# fc-paper-read

自动搜索、阅读和解读 AI 领域最新热门论文的 Claude Code 技能。

## 功能

- 🔍 自动在 arXiv 搜索最近2周内发布的论文
- 📊 智能选择最相关且热门的论文
- 📖 使用 ljg-paper-flow 深度解读论文
- 📝 自动保存到 Obsidian 知识库
- 📨 发送到飞书（可选）

## 安装

确保已安装以下依赖：

- Node.js 22+
- Chrome 浏览器（启用远程调试）
- web-access 技能
- ljg-paper-flow 技能

## 使用

```bash
# 使用默认主题（AI、LLM、Agent）
/fc-paper-read

# 指定主题搜索
/fc-paper-read "reinforcement learning"
/fc-paper-read "multimodal"
/fc-paper-read "vision transformer"
```

## 工作流程

1. **确定主题** - 使用用户输入的主题或默认主题
2. **搜索 arXiv** - 在最近2周内发布的论文中搜索
3. **选择最佳论文** - 根据相关性和热度智能选择1篇
4. **深度解读** - 使用 ljg-paper-flow 进行专业解读
5. **保存到 Obsidian** - 自动整理到知识库
6. **发送到飞书** - 通过飞书机器人推送（可选）

## 配置

复制 `config/.env.example` 到 `config/.env` 并填写配置：

```bash
cp config/.env.example config/.env
```

可选配置项：
- `DEFAULT_TOPIC`: 默认搜索主题
- `FEISHU_WEBHOOK_URL`: 飞书机器人 Webhook 地址

## 目录结构

```
fc-paper-read/
├── SKILL.md              # 技能定义文件
├── config/
│   └── .env.example      # 环境变量模板
├── scripts/
│   └── run_paper_read.py # 主执行脚本
└── data/                 # 数据存储目录（自动创建）
```

## 依赖技能

- [web-access](../web-access/) - 浏览器自动化
- [ljg-paper-flow](../ljg-paper-flow/) - 论文解读
