# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""已处理披露记录的追踪管理。"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ProcessedRecord:
    """已处理的披露记录。"""

    unique_id: str
    stock_code: str
    title: str
    date_time: str
    processed_at: str


class ProcessedTracker:
    """追踪已处理的披露信息，避免重复处理。"""

    def __init__(self, data_path: Path) -> None:
        self._file = data_path / "processed.json"
        self._records: dict[str, ProcessedRecord] = {}
        self._load()

    def _load(self) -> None:
        """从文件加载已处理记录。"""
        if not self._file.exists():
            return
        try:
            data = json.loads(self._file.read_text(encoding="utf-8"))
            for uid, record_data in data.items():
                self._records[uid] = ProcessedRecord(**record_data)
            logger.info("加载了 %d 条已处理记录", len(self._records))
        except Exception as e:
            logger.error("加载已处理记录失败: %s", e)

    def _save(self) -> None:
        """保存已处理记录到文件。"""
        self._file.parent.mkdir(parents=True, exist_ok=True)
        data = {uid: asdict(record) for uid, record in self._records.items()}
        self._file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def is_processed(self, unique_id: str) -> bool:
        """检查某条披露是否已处理。"""
        return unique_id in self._records

    def mark_processed(
        self,
        unique_id: str,
        stock_code: str,
        title: str,
        date_time: str,
    ) -> None:
        """标记某条披露为已处理。"""
        self._records[unique_id] = ProcessedRecord(
            unique_id=unique_id,
            stock_code=stock_code,
            title=title,
            date_time=date_time,
            processed_at=datetime.now().isoformat(),
        )
        self._save()
        logger.info("已标记为处理完成: %s", unique_id)

    def get_stats(self) -> dict[str, int]:
        """获取处理统计。"""
        by_stock: dict[str, int] = {}
        for record in self._records.values():
            by_stock[record.stock_code] = by_stock.get(record.stock_code, 0) + 1
        return by_stock
