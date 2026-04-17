# 架构图风格主题配置

## engineering (-e) 工程极简

**适用场景**: 技术文档、RFC、C4 模型

```yaml
BG_COLOR: "#FFFFFF"
FONT_FAMILY: "JetBrains Mono, monospace"
MERMAID_THEME: base
MERMAID_VARS:
  primaryColor: "#FFFFFF"
  primaryBorderColor: "#333333"
  primaryTextColor: "#333333"
  lineColor: "#666666"
  secondaryColor: "#F5F5F5"
  tertiaryColor: "#FFFFFF"
```

## modern (-m) 现代设计感

**适用场景**: Figma 社区图、产品架构展示

```yaml
BG_COLOR: "#F8F9FC"
FONT_FAMILY: "Geist, sans-serif"
MERMAID_THEME: base
MERMAID_VARS:
  primaryColor: "#3B5BDB"
  primaryBorderColor: "#2F4AC0"
  primaryTextColor: "#FFFFFF"
  lineColor: "#3B5BDB"
  secondaryColor: "#EEF2FF"
  tertiaryColor: "#F8F9FC"
```

## dark (-d) 暗黑风

**适用场景**: 终端风格、监控大屏、深色主题文档

```yaml
BG_COLOR: "#1A1A2E"
FONT_FAMILY: "JetBrains Mono, monospace"
MERMAID_THEME: dark
MERMAID_VARS:
  primaryColor: "#16213E"
  primaryBorderColor: "#0F3460"
  primaryTextColor: "#E0E0E0"
  lineColor: "#00B4D8"
  secondaryColor: "#1A1A2E"
  tertiaryColor: "#16213E"
```

## colorful (-c) 彩色自定义

**适用场景**: 博客配图、教学演示

**颜色映射**:
- 网关/API: #FF6B35 (橙)
- 服务: #3B5BDB (蓝)
- 存储: "#22C55E" (绿)
- 队列: "#A855F7" (紫)
- 缓存: "#F59E0B" (黄)
- 外部: "#6B7280" (灰)

```yaml
BG_COLOR: "#FAFAFA"
FONT_FAMILY: "Outfit, sans-serif"
MERMAID_THEME: base
MERMAID_VARS:
  primaryColor: "#3B5BDB"
  primaryBorderColor: "#2F4AC0"
  primaryTextColor: "#FFFFFF"
  lineColor: "#666666"
  secondaryColor: "#F3F4F6"
  tertiaryColor: "#FAFAFA"
```

## 风格快速选择指南

| 需求 | 推荐风格 |
|------|----------|
| 技术文档/架构评审 | -e |
| 产品演示/设计稿 | -m |
| 深色模式/大屏 | -d |
| 教学/博客配图 | -c |
