# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx>=0.27",
# ]
# ///
"""HKEX 信息披露 API 客户端 - 获取港股最新公告列表。

工作流程：
1. 通过 prefix API 将股票代码（如 00700）解析为 HKEX 内部 stockId
2. 用 stockId 调用 titleSearchServlet 获取披露列表
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

import httpx

logger = logging.getLogger(__name__)

HKEX_PREFIX_URL = "https://www1.hkexnews.hk/search/prefix.do"
HKEX_SEARCH_URL = "https://www1.hkexnews.hk/search/titleSearchServlet.do"

SEARCH_PARAMS: dict[str, str] = {
    "sortDir": "0",
    "sortByOptions": "DateTime",
    "category": "0",
    "market": "SEHK",
    "stockId": "",
    "fromDate": "",
    "toDate": "",
    "title": "",
    "searchType": "0",
    "t": "zh",
    "rowRange": "10",
    "lang": "ZH",
}


@dataclass
class Disclosure:
    """一条信息披露记录。"""

    stock_code: str
    stock_name: str
    title: str
    date_time: str
    file_url: str
    file_type: str
    news_id: str
    category: str = ""

    @property
    def unique_id(self) -> str:
        return f"{self.stock_code}_{self.news_id}"


@dataclass
class FetchResult:
    """抓取结果。"""

    stock_code: str
    disclosures: list[Disclosure] = field(default_factory=list)
    error: str | None = None


async def _resolve_stock_id(
    client: httpx.AsyncClient, stock_code: str
) -> int | None:
    """通过 prefix API 将股票代码解析为 HKEX 内部 stockId。"""
    params = {
        "lang": "ZH",
        "type": "A",
        "name": stock_code,
        "market": "SEHK",
        "callback": "callback",
    }
    resp = await client.get(HKEX_PREFIX_URL, params=params)
    resp.raise_for_status()

    # 解析 JSONP 响应: callback({...});\r\n
    text = resp.text.strip().rstrip(";")
    if text.startswith("callback(") and text.endswith(")"):
        text = text[9:-1]

    data = json.loads(text)
    stock_list = data.get("stockInfo", [])

    for stock in stock_list:
        if stock.get("code") == stock_code:
            return stock["stockId"]

    return None


def _clean_html(text: str) -> str:
    """清理 HTML 标签和转义字符。"""
    text = re.sub(r"<br\s*/?>", " ", text)
    text = text.replace("&#x2f;", "/").replace("&#x3b;", ";")
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def _detect_file_type(link: str) -> str:
    """根据链接推断文件类型。"""
    lower = link.lower()
    if lower.endswith(".doc") or lower.endswith(".docx"):
        return "word"
    if lower.endswith(".xls") or lower.endswith(".xlsx"):
        return "excel"
    if lower.endswith(".htm") or lower.endswith(".html"):
        return "html"
    return "pdf"


def _parse_disclosures(
    stock_code: str, raw_result: str
) -> list[Disclosure]:
    """解析 titleSearchServlet 返回的 JSON 结果。"""
    if not raw_result or raw_result == "null":
        return []

    records = json.loads(raw_result)
    if not isinstance(records, list):
        return []

    results: list[Disclosure] = []
    for record in records:
        try:
            file_link = record.get("FILE_LINK", "")
            if file_link and not file_link.startswith("http"):
                file_link = f"https://www1.hkexnews.hk{file_link}"

            # 清理股票名称中的 HTML（如 "00700<br/>80700 腾讯控股<br/>..."）
            raw_name = record.get("STOCK_NAME", "")
            stock_name = _clean_html(raw_name).split()[-1] if raw_name else ""

            results.append(Disclosure(
                stock_code=stock_code,
                stock_name=stock_name,
                title=_clean_html(record.get("TITLE", "")),
                date_time=record.get("DATE_TIME", ""),
                file_url=file_link,
                file_type=_detect_file_type(file_link),
                news_id=record.get("NEWS_ID", str(hash(file_link))),
                category=_clean_html(record.get("LONG_TEXT", "")),
            ))
        except Exception as e:
            logger.warning("解析披露记录失败: %s", e)

    return results


async def fetch_disclosures(
    stock_code: str,
    row_range: int = 10,
    timeout: float = 30.0,
) -> FetchResult:
    """获取指定港股的最新披露信息。

    Args:
        stock_code: 港股代码，如 "00700"
        row_range: 返回条数，默认 10
        timeout: 请求超时（秒）
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            # 第一步：解析内部 stockId
            internal_id = await _resolve_stock_id(client, stock_code)
            if internal_id is None:
                return FetchResult(
                    stock_code=stock_code,
                    error=f"无法解析股票代码 {stock_code} 的 HKEX 内部 ID",
                )

            # 第二步：用 GET 请求搜索披露信息
            params = {
                **SEARCH_PARAMS,
                "stockId": str(internal_id),
                "rowRange": str(row_range),
            }
            resp = await client.get(HKEX_SEARCH_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        disclosures = _parse_disclosures(stock_code, data.get("result", ""))
        logger.info("获取到 %s 的 %d 条披露信息", stock_code, len(disclosures))
        return FetchResult(stock_code=stock_code, disclosures=disclosures)

    except httpx.HTTPStatusError as e:
        msg = f"HKEX API 返回错误: {e.response.status_code}"
        logger.error(msg)
        return FetchResult(stock_code=stock_code, error=msg)
    except Exception as e:
        msg = f"请求 HKEX API 失败: {e}"
        logger.error(msg)
        return FetchResult(stock_code=stock_code, error=msg)


async def fetch_all(
    stock_codes: list[str], row_range: int = 10
) -> list[FetchResult]:
    """批量获取多只股票的披露信息。"""
    import asyncio

    tasks = [fetch_disclosures(code, row_range) for code in stock_codes]
    return await asyncio.gather(*tasks)
