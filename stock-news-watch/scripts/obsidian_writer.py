# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""将披露摘要写入 Obsidian 知识库。"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

OBSIDIAN_BASE = Path("/Users/jiangfachang/Obsidian/SecondBrain")
DISCLOSURE_DIR = OBSIDIAN_BASE / "投资" / "信息披露"


def write_disclosure_note(
    stock_name: str,
    stock_code: str,
    title: str,
    summary: str,
    file_url: str,
    date_time: str,
    category: str = "",
) -> Path | None:
    """将一条披露摘要写入 Obsidian 知识库。

    Args:
        stock_name: 股票名称
        stock_code: 股票代码
        title: 公告标题
        summary: AI 摘要
        file_url: 原文链接
        date_time: 披露时间
        category: 公告类别

    Returns:
        写入的文件路径，失败返回 None
    """
    try:
        # 确保目录存在
        stock_dir = DISCLOSURE_DIR / f"{stock_name}({stock_code})"
        stock_dir.mkdir(parents=True, exist_ok=True)

        # 生成文件名（清理非法字符）
        safe_title = _sanitize_filename(title)
        date_str = _extract_date(date_time)
        filename = f"{date_str} {safe_title}.md"
        filepath = stock_dir / filename

        # 构建笔记内容
        content = _build_note(
            stock_name, stock_code, title, summary,
            file_url, date_time, category,
        )

        filepath.write_text(content, encoding="utf-8")
        logger.info("已写入知识库: %s", filepath)
        return filepath

    except Exception as e:
        logger.error("写入知识库失败: %s", e)
        return None


def _build_note(
    stock_name: str,
    stock_code: str,
    title: str,
    summary: str,
    file_url: str,
    date_time: str,
    category: str,
) -> str:
    """构建 Obsidian Markdown 笔记内容。"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    tags_line = f"tags: [投资, {stock_name}]"
    if category:
        tags_line = f"tags: [投资, {stock_name}, {category}]"

    return f"""---
{tags_line}
stock_code: "{stock_code}"
disclosure_date: "{date_time}"
created: "{now}"
source: HKEX
---

# {title}

**股票：**{stock_name}（{stock_code}）
**披露时间：**{date_time}
**类别：**{category or "未分类"}

---

## AI 摘要

{summary}

---

**原文链接：**[查看原文]({file_url})
"""


def _sanitize_filename(name: str) -> str:
    """清理文件名中的非法字符。"""
    # 移除或替换非法字符
    name = re.sub(r'[<>:"/\\|?*]', "", name)
    # 截断过长的文件名
    if len(name) > 80:
        name = name[:80]
    return name.strip()


def _extract_date(date_time: str) -> str:
    """从日期时间字符串提取日期部分。"""
    # 尝试多种格式
    for fmt in ("%Y/%m/%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(date_time.strip(), fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    # 回退：取前10个字符或当天日期
    if len(date_time) >= 10:
        return date_time[:10].replace("/", "-")
    return datetime.now().strftime("%Y-%m-%d")
