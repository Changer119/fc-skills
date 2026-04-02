---
name: stock-news-watch
description: |
  监控港股（未来扩展到A股、美股）的信息披露情况。自动抓取 HKEX 最新披露公告，下载文件并用 AI 总结关键信息，通过飞书通知用户，同时写入 Obsidian 知识库。
  使用场景：当用户要求检查股票披露信息、监控港股公告、查看最新股票新闻、运行信息披露监控时触发。
  也适用于：用户说"检查下我的股票有没有新公告"、"港股有什么新消息"、"跑一下股票监控"等。
metadata:
  clawdbot:
    emoji: "📰"
    requires:
      bins: ["uv"]
      env: ["LLM_API_URL", "LLM_API_TOKEN", "LLM_MODEL"]
---

# Stock News Watch - 股票信息披露监控

监控港股信息披露，自动摘要并通知。

## 快速开始

运行一次完整监控（检查所有监控列表中的股票）：

```bash
uv run {baseDir}/scripts/run_watch.py
```

仅检查单只股票：

```bash
uv run {baseDir}/scripts/run_watch.py --stock 00700
```

查看当前监控列表：

```bash
uv run {baseDir}/scripts/run_watch.py --list
```

添加股票到监控列表：

```bash
uv run {baseDir}/scripts/run_watch.py --add 00700 --name "腾讯控股" --market hk
```

移除股票：

```bash
uv run {baseDir}/scripts/run_watch.py --remove 00700
```

## 配置

### 环境变量

在 `{baseDir}/config/.env` 中配置（从 `.env.example` 复制）：

- `LLM_API_URL` - 兼容 OpenAI 接口的大模型服务地址
- `LLM_API_TOKEN` - API Token
- `LLM_MODEL` - 模型名称
- `FEISHU_WEBHOOK_URL` - 飞书机器人 Webhook 地址

### 监控列表

编辑 `{baseDir}/config/watchlist.yaml` 管理监控的股票清单。

## 工作流程

1. 读取监控列表中的港股代码
2. 调用 HKEX 披露信息 API 获取最新公告
3. 对比已处理记录，筛选出新公告
4. 下载公告文件（PDF/Word/Excel 等）
5. 调用 AI 模型总结关键信息
6. 通过飞书 Webhook 推送摘要通知
7. 将摘要写入 Obsidian 知识库（标签：投资、股票名称）
8. 记录已处理状态，避免重复

## 支持的市场

- [x] 港股（HKEX）
- [ ] A股（待实现）
- [ ] 美股（待实现）

## 数据存储

- 已处理记录：`{baseDir}/data/processed.json`
- 监控列表：`{baseDir}/config/watchlist.yaml`
- 日志：`{baseDir}/data/watch.log`
