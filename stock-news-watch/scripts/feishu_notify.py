# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx>=0.27",
# ]
# ///
"""飞书 Webhook 通知模块。"""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

SIGNATURE_KEYWORD = "股票信息披露Bot"


async def send_feishu_notification(
    webhook_url: str,
    stock_name: str,
    stock_code: str,
    title: str,
    summary: str,
    file_url: str,
    date_time: str,
) -> bool:
    """通过飞书 Webhook 发送披露信息通知。

    Args:
        webhook_url: 飞书机器人 Webhook 地址
        stock_name: 股票名称
        stock_code: 股票代码
        title: 公告标题
        summary: AI 摘要内容
        file_url: 原文链接
        date_time: 披露时间

    Returns:
        是否发送成功
    """
    content = _build_message(
        stock_name, stock_code, title, summary, file_url, date_time
    )

    payload = {
        "msg_type": "interactive",
        "card": content,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(webhook_url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        if data.get("code") == 0 or data.get("StatusCode") == 0:
            logger.info("飞书通知发送成功: %s - %s", stock_code, title)
            return True

        logger.error("飞书通知返回错误: %s", data)
        return False

    except Exception as e:
        logger.error("飞书通知发送失败: %s", e)
        return False


def _build_message(
    stock_name: str,
    stock_code: str,
    title: str,
    summary: str,
    file_url: str,
    date_time: str,
) -> dict:
    """构建飞书卡片消息。"""
    return {
        "header": {
            "template": "blue",
            "title": {
                "tag": "plain_text",
                "content": f"📢 {stock_name}({stock_code}) 信息披露",
            },
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**公告标题：**{title}",
                },
            },
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**披露时间：**{date_time}",
                },
            },
            {"tag": "hr"},
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**AI 摘要：**\n{summary}",
                },
            },
            {"tag": "hr"},
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {
                            "tag": "plain_text",
                            "content": "查看原文",
                        },
                        "url": file_url,
                        "type": "primary",
                    }
                ],
            },
            {
                "tag": "note",
                "elements": [
                    {
                        "tag": "plain_text",
                        "content": f"from {SIGNATURE_KEYWORD}",
                    }
                ],
            },
        ],
    }


async def send_feishu_text(webhook_url: str, text: str) -> bool:
    """发送纯文本消息（用于错误通知等简单场景）。"""
    content = f"{text}\n\nfrom {SIGNATURE_KEYWORD}"
    payload = {
        "msg_type": "text",
        "content": {"text": content},
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(webhook_url, json=payload)
            resp.raise_for_status()
            return True
    except Exception as e:
        logger.error("飞书文本通知发送失败: %s", e)
        return False
