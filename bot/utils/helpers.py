"""通用工具函数"""


def truncate(text: str, max_len: int = 300) -> str:
    """截断文本"""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def safe_int(value: str, default: int = 0) -> int:
    """安全转换为整数"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default
