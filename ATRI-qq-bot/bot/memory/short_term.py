"""短期记忆 (环形缓冲区)"""

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Turn:
    role: str          # "user" | "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    emotion: str = ""
    affection_delta: int = 0


class ShortTermMemory:
    """短期记忆，环形缓冲区保存最近 N 轮对话"""

    def __init__(self, max_turns: int = 30):
        self.buffer: deque[Turn] = deque(maxlen=max_turns)

    def add_turn(self, turn: Turn):
        self.buffer.append(turn)

    def get_context(self) -> list[dict]:
        """返回消息列表格式的上下文"""
        return [
            {"role": t.role, "content": t.content}
            for t in self.buffer
        ]

    def get_turns(self) -> list[Turn]:
        return list(self.buffer)

    def should_consolidate(self) -> bool:
        """缓冲区满时触发记忆压缩"""
        return len(self.buffer) >= self.buffer.maxlen

    def pop_oldest(self, count: int) -> list[Turn]:
        """取出最旧的 N 条记录"""
        result = []
        for _ in range(min(count, len(self.buffer))):
            result.append(self.buffer.popleft())
        return result

    def clear(self):
        self.buffer.clear()

    def __len__(self) -> int:
        return len(self.buffer)
