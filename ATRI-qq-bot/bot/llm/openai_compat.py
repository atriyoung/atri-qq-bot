"""OpenAI 兼容 API 客户端

支持 DeepSeek、通义千问等所有 OpenAI 兼容接口的模型。
"""

import asyncio
from openai import AsyncOpenAI
from openai import (
    APIError,
    APIConnectionError,
    APITimeoutError as OpenAITimeoutError,
    RateLimitError as OpenAIRateLimitError,
)

from loguru import logger

from .base import BaseLLMClient
from .errors import (
    LLMError,
    RateLimitError,
    ContentFilterError,
    APITimeoutError as LLMAPITimeoutError,
    APIConnectionError as LLMAPIConnectionError,
)


class OpenAICompatClient(BaseLLMClient):
    """OpenAI 兼容 API 客户端"""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        max_retries: int = 2,
        timeout: float = 30.0,
    ):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=0,  # 我们自己控制重试
        )
        self.model = model
        self.max_retries = max_retries

    async def chat(
        self,
        messages: list[dict],
        temperature: float = 0.8,
        max_tokens: int = 512,
    ) -> str:
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                content = resp.choices[0].message.content
                return content.strip() if content else "..."

            except OpenAIRateLimitError as e:
                last_error = e
                if attempt < self.max_retries:
                    wait = 2 ** attempt
                    logger.warning(f"Rate limited, retrying in {wait}s (attempt {attempt + 1})")
                    await asyncio.sleep(wait)
                else:
                    raise RateLimitError(f"Rate limit exceeded: {e}") from e

            except OpenAITimeoutError as e:
                raise LLMAPITimeoutError(f"API timeout: {e}") from e

            except APIConnectionError as e:
                raise LLMAPIConnectionError(f"API connection failed: {e}") from e

            except APIError as e:
                error_msg = str(e).lower()
                # 内容过滤
                if any(kw in error_msg for kw in ("content_filter", "safety", "blocked", "refused")):
                    raise ContentFilterError(f"Content filtered: {e}") from e
                # 其他 API 错误
                if attempt < self.max_retries:
                    wait = 2 ** attempt
                    logger.warning(f"API error, retrying in {wait}s: {e}")
                    await asyncio.sleep(wait)
                else:
                    raise LLMError(f"API error: {e}") from e

        raise LLMError(f"Max retries exceeded: {last_error}")
