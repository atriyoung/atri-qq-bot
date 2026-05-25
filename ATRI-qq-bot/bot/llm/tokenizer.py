"""简易 Token 估算

中文字符约等于 1.5-2 个 token，英文字符约 0.3 个 token。
这里使用保守估算。
"""


def estimate_tokens(text: str) -> int:
    """估算文本的 token 数量"""
    count = 0
    for char in text:
        if '一' <= char <= '鿿' or '　' <= char <= '〿':
            # 中文字符范围
            count += 2
        else:
            count += 1
    # 粗略按 3.5 字符/token 折算
    return count // 3 + 1


def estimate_messages_tokens(messages: list[dict]) -> int:
    """估算消息列表的总 token 数"""
    total = 0
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            total += estimate_tokens(content)
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and "text" in part:
                    total += estimate_tokens(part["text"])
        total += 4  # 消息格式开销
    return total
