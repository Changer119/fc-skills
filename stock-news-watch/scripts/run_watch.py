# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx>=0.27",
#     "pypdf>=4.0",
#     "python-docx>=1.1",
#     "openpyxl>=3.1",
#     "pyyaml>=6.0",
#     "python-dotenv>=1.0",
# ]
# ///
"""股票信息披露监控 - 主入口脚本。"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# 脚本所在目录
SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
CONFIG_DIR = SKILL_DIR / "config"
DATA_DIR = SKILL_DIR / "data"
LOG_FILE = DATA_DIR / "watch.log"


def setup_logging() -> None:
    """配置日志输出到文件和控制台。"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def load_env() -> None:
    """加载环境变量。"""
    from dotenv import load_dotenv

    env_file = CONFIG_DIR / ".env"
    if env_file.exists():
        load_dotenv(env_file)


def load_watchlist() -> list[dict]:
    """加载监控列表。"""
    import yaml

    watchlist_file = CONFIG_DIR / "watchlist.yaml"
    if not watchlist_file.exists():
        logging.error("监控列表不存在: %s", watchlist_file)
        return []

    data = yaml.safe_load(watchlist_file.read_text(encoding="utf-8"))
    return data.get("stocks", [])


def get_llm_config():
    """获取大模型配置。"""
    import os
    from doc_summarizer import LLMConfig

    return LLMConfig(
        api_url=os.environ.get("LLM_API_URL", ""),
        api_token=os.environ.get("LLM_API_TOKEN", ""),
        model=os.environ.get("LLM_MODEL", ""),
    )


def get_feishu_webhook() -> str:
    """获取飞书 Webhook 地址。"""
    import os

    return os.environ.get("FEISHU_WEBHOOK_URL", "")


async def watch_single_stock(
    stock: dict,
    tracker,
    llm_config,
    feishu_url: str,
) -> int:
    """监控单只股票的披露信息。返回新处理的条数。"""
    from hkex_fetcher import fetch_disclosures
    from doc_summarizer import summarize_disclosure
    from feishu_notify import send_feishu_notification
    from obsidian_writer import write_disclosure_note

    logger = logging.getLogger(__name__)
    code = stock["code"]
    name = stock["name"]
    market = stock.get("market", "hk")

    if market != "hk":
        logger.info("跳过非港股: %s (%s)", code, market)
        return 0

    logger.info("正在检查 %s(%s) 的最新披露...", name, code)

    # 获取最新披露
    result = await fetch_disclosures(code)
    if result.error:
        logger.error("获取 %s 披露失败: %s", code, result.error)
        return 0

    if not result.disclosures:
        logger.info("%s 无披露信息", code)
        return 0

    # 筛选未处理的新公告
    new_count = 0
    for disclosure in result.disclosures:
        if tracker.is_processed(disclosure.unique_id):
            continue

        logger.info("发现新公告: %s - %s", code, disclosure.title)

        # AI 摘要（需要 LLM 配置）
        if llm_config.api_url and llm_config.api_token:
            summary_result = await summarize_disclosure(
                file_url=disclosure.file_url,
                file_type=disclosure.file_type,
                title=disclosure.title,
                stock_name=name,
                llm_config=llm_config,
            )
            summary_text = summary_result.summary if summary_result.success else (
                f"摘要生成失败: {summary_result.error}\n原文链接: {disclosure.file_url}"
            )
        else:
            summary_text = f"（未配置 AI 模型，无法生成摘要）\n原文链接: {disclosure.file_url}"

        # 飞书通知
        if feishu_url:
            await send_feishu_notification(
                webhook_url=feishu_url,
                stock_name=name,
                stock_code=code,
                title=disclosure.title,
                summary=summary_text,
                file_url=disclosure.file_url,
                date_time=disclosure.date_time,
            )

        # 写入 Obsidian 知识库
        write_disclosure_note(
            stock_name=name,
            stock_code=code,
            title=disclosure.title,
            summary=summary_text,
            file_url=disclosure.file_url,
            date_time=disclosure.date_time,
            category=disclosure.category,
        )

        # 标记为已处理
        tracker.mark_processed(
            unique_id=disclosure.unique_id,
            stock_code=code,
            title=disclosure.title,
            date_time=disclosure.date_time,
        )
        new_count += 1

    return new_count


async def run_watch(target_stock: str | None = None) -> None:
    """运行完整监控流程。"""
    from tracker import ProcessedTracker

    logger = logging.getLogger(__name__)
    watchlist = load_watchlist()

    if not watchlist:
        logger.error("监控列表为空，请先配置 watchlist.yaml")
        print("监控列表为空。请编辑配置文件添加股票:")
        print(f"  {CONFIG_DIR / 'watchlist.yaml'}")
        return

    # 如果指定了单只股票
    if target_stock:
        watchlist = [s for s in watchlist if s["code"] == target_stock]
        if not watchlist:
            print(f"股票 {target_stock} 不在监控列表中")
            return

    tracker = ProcessedTracker(DATA_DIR)
    llm_config = get_llm_config()
    feishu_url = get_feishu_webhook()

    if not llm_config.api_url or not llm_config.api_token:
        logger.warning("未配置 LLM API，将跳过 AI 摘要")

    if not feishu_url:
        logger.warning("未配置飞书 Webhook，将跳过通知推送")

    total_new = 0
    for stock in watchlist:
        count = await watch_single_stock(stock, tracker, llm_config, feishu_url)
        total_new += count

    # 输出统计
    if total_new > 0:
        print(f"\n✅ 本次共处理 {total_new} 条新披露信息")
    else:
        print("\n📭 没有新的披露信息")

    stats = tracker.get_stats()
    if stats:
        print("\n累计处理统计:")
        for code, count in stats.items():
            print(f"  {code}: {count} 条")


def handle_add(args) -> None:
    """添加股票到监控列表。"""
    import yaml

    watchlist_file = CONFIG_DIR / "watchlist.yaml"
    if watchlist_file.exists():
        data = yaml.safe_load(watchlist_file.read_text(encoding="utf-8")) or {}
    else:
        data = {}

    stocks = data.get("stocks", [])

    # 检查是否已存在
    for s in stocks:
        if s["code"] == args.add:
            print(f"股票 {args.add} 已在监控列表中")
            return

    stocks.append({
        "code": args.add,
        "name": args.name or args.add,
        "market": args.market or "hk",
    })
    data["stocks"] = stocks

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    watchlist_file.write_text(
        yaml.dump(data, allow_unicode=True, default_flow_style=False),
        encoding="utf-8",
    )
    print(f"✅ 已添加 {args.name or args.add}({args.add}) 到监控列表")


def handle_remove(args) -> None:
    """从监控列表移除股票。"""
    import yaml

    watchlist_file = CONFIG_DIR / "watchlist.yaml"
    if not watchlist_file.exists():
        print("监控列表不存在")
        return

    data = yaml.safe_load(watchlist_file.read_text(encoding="utf-8")) or {}
    stocks = data.get("stocks", [])
    original_len = len(stocks)
    stocks = [s for s in stocks if s["code"] != args.remove]

    if len(stocks) == original_len:
        print(f"股票 {args.remove} 不在监控列表中")
        return

    data["stocks"] = stocks
    watchlist_file.write_text(
        yaml.dump(data, allow_unicode=True, default_flow_style=False),
        encoding="utf-8",
    )
    print(f"✅ 已从监控列表移除 {args.remove}")


def handle_list() -> None:
    """显示当前监控列表。"""
    watchlist = load_watchlist()
    if not watchlist:
        print("监控列表为空")
        return

    print("当前监控列表:")
    print(f"{'代码':<10} {'名称':<15} {'市场':<6}")
    print("-" * 35)
    for stock in watchlist:
        print(f"{stock['code']:<10} {stock['name']:<15} {stock.get('market', 'hk'):<6}")


def main() -> None:
    parser = argparse.ArgumentParser(description="股票信息披露监控")
    parser.add_argument("--stock", help="仅检查指定股票代码")
    parser.add_argument("--list", action="store_true", help="显示监控列表")
    parser.add_argument("--add", help="添加股票代码到监控列表")
    parser.add_argument("--name", help="股票名称（配合 --add 使用）")
    parser.add_argument("--market", default="hk", help="市场类型（默认 hk）")
    parser.add_argument("--remove", help="从监控列表移除股票代码")

    args = parser.parse_args()

    setup_logging()
    load_env()

    # 将脚本目录加入 sys.path 以便导入同目录模块
    if str(SCRIPT_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPT_DIR))

    if args.list:
        handle_list()
    elif args.add:
        handle_add(args)
    elif args.remove:
        handle_remove(args)
    else:
        asyncio.run(run_watch(target_stock=args.stock))


if __name__ == "__main__":
    main()
