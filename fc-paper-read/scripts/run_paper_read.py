#!/usr/bin/env python3
"""
fc-paper-read: 自动搜索和阅读 AI 论文

工作流程：
1. 确定主题（用户提供或使用默认）
2. 搜索 arXiv 最近2周的热门论文
3. 选择最佳论文
4. 调用 ljg-paper-flow 深度解读
5. 保存到 Obsidian
6. 发送到飞书（可选）
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from urllib.parse import quote


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 默认主题
DEFAULT_TOPIC = "AI OR LLM OR Agent OR \"large language model\" OR \"artificial intelligence\""

# 目录配置
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config"
OBSIDIAN_DIR = Path.home() / "Obsidian" / "SecondBrain" / "论文" / "AI论文"


def get_date_range() -> tuple[str, str]:
    """获取最近2周的日期范围"""
    today = datetime.now()
    two_weeks_ago = today - timedelta(days=14)

    # arXiv 日期格式: YYYY-MM-DD
    return (
        two_weeks_ago.strftime("%Y-%m-%d"),
        today.strftime("%Y-%m-%d")
    )


def build_arxiv_search_url(topic: str) -> str:
    """构建 arXiv 高级搜索 URL"""
    from_date, to_date = get_date_range()

    # URL 编码主题
    encoded_topic = quote(topic)

    # 构建 URL
    url = (
        f"https://arxiv.org/search/advanced?"
        f"query={encoded_topic}&"
        f"classification=cs&"
        f"date-date_type=submitted_date&"
        f"date-from_date={from_date}&"
        f"date-to_date={to_date}&"
        f"order=-announced_date_first&"
        f"size=25"  # 每页25篇
    )

    return url


def check_web_access_deps() -> bool:
    """检查 web-access 依赖"""
    try:
        skill_dir = os.environ.get("CLAUDE_SKILL_DIR", "")
        if not skill_dir:
            # 尝试默认路径
            skill_dir = str(Path.home() / ".claude" / "skills" / "web-access")

        check_script = Path(skill_dir) / "scripts" / "check-deps.mjs"
        if not check_script.exists():
            logger.error(f"web-access check script not found: {check_script}")
            return False

        result = subprocess.run(
            ["node", str(check_script)],
            capture_output=True,
            text=True,
            timeout=30
        )

        return result.returncode == 0

    except Exception as e:
        logger.error(f"Failed to check web-access deps: {e}")
        return False


def search_papers(topic: str) -> list[dict]:
    """
    使用浏览器 CDP 搜索 arXiv 论文

    返回论文列表，每篇包含：title, url, authors, abstract, date
    """
    logger.info(f"正在搜索主题: {topic}")

    # 检查依赖
    if not check_web_access_deps():
        logger.error("web-access 依赖检查失败")
        return []

    search_url = build_arxiv_search_url(topic)
    logger.info(f"搜索 URL: {search_url}")

    try:
        # 1. 创建新 tab 打开搜索页面
        logger.info("正在打开 arXiv 搜索页面...")
        result = subprocess.run(
            ["curl", "-s", f"http://localhost:3456/new?url={search_url}"],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            logger.error(f"Failed to open arXiv: {result.stderr}")
            return []

        try:
            response = json.loads(result.stdout)
            target_id = response.get("targetId")
        except json.JSONDecodeError:
            # 可能直接返回 targetId
            target_id = result.stdout.strip()

        if not target_id:
            logger.error("Failed to get target ID")
            return []

        logger.info(f"Target ID: {target_id}")

        # 等待页面加载
        time.sleep(3)

        # 2. 提取论文信息
        logger.info("正在提取论文列表...")
        extract_script = '''
        (() => {
            const papers = [];
            const items = document.querySelectorAll("li.arxiv-result");

            items.forEach(item => {
                const titleEl = item.querySelector("p.title");
                const linkEl = item.querySelector("a[href*=\\"/abs/\\"]");
                const authorsEl = item.querySelector("p.authors");
                const abstractEl = item.querySelector("p.abstract");
                const dateEl = item.querySelector("p.is-size-7");

                if (titleEl && linkEl) {
                    const title = titleEl.textContent.trim();
                    let url = linkEl.href;
                    // 确保是完整 URL
                    if (url.startsWith("/")) {
                        url = "https://arxiv.org" + url;
                    }

                    papers.push({
                        title: title,
                        url: url,
                        authors: authorsEl ? authorsEl.textContent.replace("Authors:", "").trim() : "",
                        abstract: abstractEl ? abstractEl.textContent.trim().substring(0, 500) : "",
                        date: dateEl ? dateEl.textContent.trim() : ""
                    });
                }
            });

            return JSON.stringify(papers);
        })()
        '''

        result = subprocess.run(
            [
                "curl", "-s", "-X", "POST",
                f"http://localhost:3456/eval?target={target_id}",
                "-d", extract_script
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        # 关闭 tab
        subprocess.run(
            ["curl", "-s", f"http://localhost:3456/close?target={target_id}"],
            capture_output=True,
            timeout=10
        )

        if result.returncode != 0:
            logger.error(f"Failed to extract papers: {result.stderr}")
            return []

        # 解析结果
        try:
            papers = json.loads(result.stdout)
            logger.info(f"找到 {len(papers)} 篇论文")
            return papers
        except json.JSONDecodeError:
            logger.error(f"Failed to parse papers JSON: {result.stdout}")
            return []

    except subprocess.TimeoutExpired:
        logger.error("Search timeout")
        return []
    except Exception as e:
        logger.error(f"Error searching papers: {e}")
        return []


def select_best_paper(papers: list[dict], topic: str) -> Optional[dict]:
    """
    从论文列表中选择最佳论文

    选择标准：
    1. 与主题的相关性
    2. 发布时间的远近（越新越好）
    3. 标题和摘要的质量
    """
    if not papers:
        return None

    logger.info(f"从 {len(papers)} 篇论文中选择最佳论文...")

    # 简单评分：包含关键词的加分
    topic_keywords = topic.lower().split()
    scored_papers = []

    for paper in papers:
        score = 0
        title_lower = paper.get("title", "").lower()
        abstract_lower = paper.get("abstract", "").lower()

        # 关键词匹配
        for keyword in topic_keywords:
            keyword = keyword.strip('"').lower()
            if keyword in title_lower:
                score += 10
            if keyword in abstract_lower:
                score += 5

        # 标题长度适中（不要太短也不要太长）
        title_len = len(paper.get("title", ""))
        if 30 < title_len < 150:
            score += 3

        scored_papers.append((score, paper))

    # 按分数排序，返回最高分
    scored_papers.sort(key=lambda x: x[0], reverse=True)
    best_paper = scored_papers[0][1]

    logger.info(f"选定论文: {best_paper.get('title', 'Unknown')[:60]}...")
    return best_paper


def save_to_obsidian(paper_info: dict, content: str) -> Path:
    """将论文解读保存到 Obsidian"""
    OBSIDIAN_DIR.mkdir(parents=True, exist_ok=True)

    # 生成文件名（使用论文标题的简化版本）
    title = paper_info.get("title", "unknown")
    safe_title = re.sub(r'[^\\w\\s-]', '', title)[:50].strip()
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_str}-{safe_title}.md"
    filepath = OBSIDIAN_DIR / filename

    # 构建 frontmatter
    frontmatter = f"""---
date: {date_str}
source: arXiv
tags:
  - 论文
  - AI
arxiv_url: {paper_info.get('url', '')}
authors: {paper_info.get('authors', '')}
---

"""

    # 写入文件
    full_content = frontmatter + content
    filepath.write_text(full_content, encoding="utf-8")

    logger.info(f"已保存到 Obsidian: {filepath}")
    return filepath


def main():
    parser = argparse.ArgumentParser(description="自动搜索和阅读 AI 论文")
    parser.add_argument(
        "topic",
        nargs="?",
        default=DEFAULT_TOPIC,
        help=f"搜索主题（默认: {DEFAULT_TOPIC}）"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="列出找到的所有论文"
    )
    parser.add_argument(
        "--select",
        type=int,
        default=0,
        help="选择第 N 篇论文（从1开始，0表示自动选择）"
    )

    args = parser.parse_args()

    # 确保数据目录存在
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 搜索论文
    papers = search_papers(args.topic)

    if not papers:
        print("❌ 未找到相关论文")
        return 1

    # 列出模式
    if args.list:
        print(f"\n找到 {len(papers)} 篇论文:\n")
        for i, paper in enumerate(papers, 1):
            print(f"{i}. {paper.get('title', 'Unknown')}")
            print(f"   作者: {paper.get('authors', 'Unknown')[:50]}...")
            print(f"   链接: {paper.get('url', 'N/A')}")
            print(f"   摘要: {paper.get('abstract', 'N/A')[:100]}...\n")
        return 0

    # 选择论文
    if args.select > 0 and args.select <= len(papers):
        selected_paper = papers[args.select - 1]
    else:
        selected_paper = select_best_paper(papers, args.topic)

    if not selected_paper:
        print("❌ 无法选择合适的论文")
        return 1

    print(f"\n✅ 选定论文: {selected_paper.get('title')}")
    print(f"   链接: {selected_paper.get('url')}")
    print(f"   作者: {selected_paper.get('authors')}")

    # 输出选中的论文信息，供后续流程使用
    output = {
        "paper": selected_paper,
        "search_topic": args.topic,
        "timestamp": datetime.now().isoformat()
    }

    # 保存到临时文件
    result_file = DATA_DIR / "selected_paper.json"
    result_file.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n📄 论文信息已保存: {result_file}")
    print("下一步: 调用 ljg-paper-flow 进行深度解读")

    return 0


if __name__ == "__main__":
    sys.exit(main())
