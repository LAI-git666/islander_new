# utils.py
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

def load_json(filepath: str) -> Any:
    """加载 JSON 文件，如果不存在返回 None"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        return None
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in {filepath}")
        return None

def save_json(filepath: str, data: Any):
    """保存数据为 JSON 文件 (覆盖模式)"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to save JSON to {filepath}: {e}")

def append_log(filepath: str, log_entry: dict):
    """
    以 JSONL 格式追加日志 (每一行是一个完整的 JSON 对象)。
    """
    try:
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.error(f"Failed to append log to {filepath}: {e}")