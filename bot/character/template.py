"""Prompt 模板辅助"""


def format_memory_context(memories: list[str]) -> str:
    """格式化长期记忆为上下文注入"""
    if not memories:
        return ""
    lines = ["【相关记忆】"]
    for i, mem in enumerate(memories, 1):
        lines.append(f"{i}. {mem}")
    return "\n".join(lines)


def build_chat_messages(
    system_prompt: str,
    recent_context: list[dict],
    user_message: str,
    memory_context: str = "",
) -> list[dict]:
    """组装完整的对话 messages 列表"""
    messages = [{"role": "system", "content": system_prompt}]

    # 注入长期记忆
    if memory_context:
        messages.append({
            "role": "system",
            "content": memory_context,
        })

    # 短期对话历史
    messages.extend(recent_context)

    # 当前用户消息
    messages.append({"role": "user", "content": user_message})

    return messages


# 安全降级回复模板
SAFE_FALLBACKS = [
    "啊...这个话题我们先跳过好不好？(>_<)",
    "唔...我不太懂这个呢，我们聊点别的吧~",
    "诶？(歪头) 你在说什么呀，我没听清楚呢...",
    "那个...我们换个话题好不好？(//▽//)",
]

# 错误降级回复模板
ERROR_FALLBACKS = [
    "唔...我刚刚走神了，能再说一遍吗？(>_<)",
    "诶？信号不太好呢...你刚才说什么？",
    "抱歉抱歉，我刚才在想别的事情...(小声)能再说一次吗？",
]
