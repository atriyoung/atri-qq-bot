"""LLM 客户端抽象基类"""

from abc import ABC, abstractmethod
from typing import AsyncIterator


class BaseLLMClient(ABC):
    """LLM 客户端抽象基类"""

    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
        temperature: float = 0.8,
        max_tokens: int = 512,
    ) -> str:
        """发送对话请求，返回回复文本"""
        ...

    async def chat_stream(
        self,
        messages: list[dict],
        temperature: float = 0.8,
        max_tokens: int = 512,
    ) -> AsyncIterator[str]:
        """流式对话（默认通过非流式模拟）"""
        result = await self.chat(messages, temperature, max_tokens)
        yield result
